import datetime
import logging
import os.path
import shutil
import tempfile
import uuid
from glob import glob, iglob
from os import unlink, makedirs, link, symlink
from os.path import dirname, join, basename
from typing import Optional

import luigi
import luigi.task
import pandas as pd
import requests
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask
from bioluigi.tasks import fastqc, multiqc
from bioluigi.tasks.cellranger import CellRangerCount
from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask
from bioluigi.tasks.utils import TaskWithOutputMixin
from luigi import WrapperTask
from luigi.task import flatten, flatten_output
from luigi.util import requires

from rnaseq_pipeline.config import Config
from .gemma import GemmaAssayType, GemmaTaskMixin, GemmaConfig, gemma_api
from .gemma import GemmaCliTask
from .sources.arrayexpress import DownloadArrayExpressSample, DownloadArrayExpressExperiment
from .sources.gemma import DownloadGemmaExperiment
from .sources.geo import DownloadGeoSample, DownloadGeoSeries
from .sources.geo import ExtractGeoSeriesBatchInfo
from .sources.local import DownloadLocalSample, DownloadLocalExperiment
from .sources.sra import DownloadSraProject, DownloadSraExperiment
from .sources.sra import ExtractSraProjectBatchInfo
from .targets import GemmaDatasetHasBatch, GemmaDatasetQuantitationType, GemmaDataVectorType, \
    RsemReference
from .utils import RerunnableTaskMixin, no_retry
from .utils import remove_task_output

logger = logging.getLogger(__name__)

cfg = Config()
gemma_cfg = GemmaConfig()

class DownloadSample(TaskWithOutputMixin, luigi.WrapperTask):
    """
    This is a generic task for downloading an individual sample in an
    experiment.

    Note that the 'gemma' source does not provide individual samples.

    The output of this task is a list (or nested list) of DownloadRunTarget.
    """
    experiment_id: str = luigi.Parameter()
    sample_id: str = luigi.Parameter()

    source = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'arrayexpress', 'local', 'sra'],
                                   positional=False)

    def requires(self):
        if self.source in ['geo', 'gemma']:
            return DownloadGeoSample(self.sample_id,
                                     metadata=dict(experiment_id=self.experiment_id, sample_id=self.sample_id))
        elif self.source == 'sra':
            return DownloadSraExperiment(self.sample_id,
                                         metadata=dict(experiment_id=self.experiment_id, sample_id=self.sample_id))
        elif self.source == 'arrayexpress':
            return DownloadArrayExpressSample(self.experiment_id, self.sample_id)
        elif self.source == 'local':
            return DownloadLocalSample(self.experiment_id, self.sample_id)
        else:
            raise ValueError('Unknown source for sample: {}.'.format(self.source))

class DownloadExperiment(TaskWithOutputMixin, luigi.WrapperTask):
    """
    This is a generic task that detects which kind of experiment is intended to
    be downloaded so that downstream tasks can process regardless of the data
    source.

    :source: Indicate the origin of the experiment, otherwise it will be
    inferred from the :experiment_id: parameter.
    """
    experiment_id = luigi.Parameter()

    source = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'sra', 'arrayexpress', 'local'],
                                   positional=False)

    def requires(self):
        if self.source == 'gemma':
            return DownloadGemmaExperiment(experiment_id=self.experiment_id)
        elif self.source == 'geo':
            return DownloadGeoSeries(experiment_id=self.experiment_id)
        elif self.source == 'sra':
            return DownloadSraProject(experiment_id=self.experiment_id)
        elif self.source == 'arrayexpress':
            return DownloadArrayExpressExperiment(experiment_id=self.experiment_id)
        elif self.source == 'local':
            return DownloadLocalExperiment(experiment_id=self.experiment_id)
        else:
            raise ValueError('Unknown download source for experiment: {}.')

@requires(DownloadSample)
class TrimSample(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Trim Illumina Universal Adapter from single end and paired reads.
    :attr ignore_mate: Ignore either the forward or reverse mate in the case of
                       paired reads, defaults to neither.
    """
    experiment_id: str
    sample_id: str

    ignore_mate = luigi.ChoiceParameter(choices=['forward', 'reverse', 'neither'], default='neither', positional=False)
    minimum_length = luigi.IntParameter(default=25, positional=False)

    def run(self):
        download_sample_task = self.requires()
        platform = download_sample_task.requires().platform
        tasks = []
        for lane in flatten(self.input()):
            destdir = join(cfg.OUTPUT_DIR, 'data-trimmed', self.experiment_id, self.sample_id, lane.run_id)
            if 'R3' in lane.layout or 'R4' in lane.layout:
                raise NotImplementedError('Trimming more than two mates is not supported.')
            elif 'R1' in lane.layout and 'R2' in lane.layout:
                r1, r2 = lane.files[lane.layout.index('R1')], lane.files[lane.layout.index('R2')]
                if self.ignore_mate == 'forward':
                    logger.info('Forward mate is ignored for %s.', repr(self))
                    tasks.append(platform.get_trim_single_end_reads_task(
                        r2,
                        join(destdir, basename(r2)),
                        minimum_length=self.minimum_length,
                        report_file=join(destdir, basename(r2) + '.cutadapt.json'),
                        cpus=4))
                elif self.ignore_mate == 'reverse':
                    logger.info('Reverse mate is ignored for %s.', repr(self))
                    tasks.append(platform.get_trim_single_end_reads_task(
                        r1,
                        join(destdir, basename(r1)),
                        minimum_length=self.minimum_length,
                        report_file=join(destdir, basename(r1) + '.cutadapt.json'),
                        cpus=4))
                else:
                    tasks.append(platform.get_trim_paired_reads_task(
                        r1, r2,
                        join(destdir, basename(r1)),
                        join(destdir, basename(r2)),
                        minimum_length=self.minimum_length,
                        report_file=join(destdir, basename(r1) + '___' + basename(r2) + '.cutadapt.json'),
                        cpus=4))
            elif 'R1' in lane.layout:
                r1 = lane.files[lane.layout.index('R1')]
                tasks.append(platform.get_trim_single_end_reads_task(
                    r1,
                    join(destdir, basename(r1)),
                    minimum_length=self.minimum_length,
                    report_file=join(destdir, basename(r1) + '.cutadapt.json'),
                    cpus=4))
            elif 'R2' in lane.layout:
                logging.warning('Found an unpaired reverse read in run %s, will treat it as single-end.', lane.run_id)
                r2 = lane.files[lane.layout.index('R2')]
                tasks.append(platform.get_trim_single_end_reads_task(
                    r2,
                    join(destdir, basename(r2)),
                    minimum_length=self.minimum_length,
                    report_file=join(destdir, basename(r2) + '.cutadapt.json'),
                    cpus=4))
            else:
                raise NotImplementedError('Unsupported lane layout: ' + '|'.join(lane.layout) + '.')
        yield tasks

class TrimExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Quality control all the samples in a given experiment.
    """
    experiment_id = luigi.Parameter()
    source = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'sra', 'arrayexpress', 'local'],
                                   positional=False)

    def requires(self):
        return DownloadExperiment(self.experiment_id, source=self.source).requires().requires()

    def run(self):
        download_sample_tasks = next(DownloadExperiment(self.experiment_id, source=self.source).requires().run())
        yield [TrimSample(self.experiment_id, dst.sample_id, source=self.source)
               for dst in download_sample_tasks]

@no_retry
@requires(TrimSample)
class QualityControlSample(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Perform post-download quality control on the FASTQs.
    """
    experiment_id: str
    sample_id: str

    def run(self):
        yield [fastqc.GenerateReport(fastq_in.path,
                                     # for bamtofastq output, include the directory name to avoid lane collisions
                                     output_dir=self._get_destdir(fastq_in),
                                     temp_dir=tempfile.gettempdir())
               for lane in self.input() for fastq_in in lane]

    def _get_destdir(self, fastq_in: luigi.LocalTarget):
        # TODO: make the run_id part of the output of TrimSample
        run_id = basename(dirname(fastq_in.path))
        # fastqc output is a directory, so to make this atomic, we need a sub-directory for each file being QCed
        filename = str(basename(fastq_in.path).removesuffix('.fastq.gz'))
        return join(cfg.OUTPUT_DIR, cfg.DATAQCDIR, self.experiment_id, self.sample_id, run_id, filename)

class QualityControlExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Quality control all the samples in a given experiment.
    """
    experiment_id = luigi.Parameter()
    source = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'sra', 'arrayexpress', 'local'],
                                   positional=False)

    def requires(self):
        return DownloadExperiment(self.experiment_id, source=self.source).requires().requires()

    def run(self):
        download_sample_tasks = next(DownloadExperiment(self.experiment_id, source=self.source).requires().run())
        yield [QualityControlSample(self.experiment_id,
                                    dst.sample_id,
                                    source=self.source)
               for dst in download_sample_tasks]

@no_retry
class PrepareReference(ScheduledExternalProgramTask):
    """
    Prepare a STAR/RSEM reference.

    :param taxon: Taxon
    :param reference_id: Reference annotation build to use (i.e. ensembl98, hg38_ncbi)
    """
    taxon: str = luigi.Parameter()
    reference_id: str = luigi.Parameter()

    cpus = 16
    memory = 32

    def input(self):
        genome_dir = join(cfg.OUTPUT_DIR, cfg.GENOMES, self.reference_id)
        gtf_files = glob(join(genome_dir, '*.gtf'))
        fasta_files = glob(join(genome_dir, '*.f*a'))  # FIXME: this pattern is too broad
        if len(gtf_files) != 1:
            raise ValueError('Exactly one GTF file is expected in {}.'.format(genome_dir))
        if len(fasta_files) < 1:
            raise ValueError(
                'At least one FASTA (with .fa or .fna extension) file is expected in {}.'.format(genome_dir))
        return [luigi.LocalTarget(gtf_files[0]),
                [luigi.LocalTarget(f) for f in fasta_files]]

    def program_args(self):
        gtf, genome_fasta = self.input()
        args = [join(cfg.RSEM_DIR, 'rsem-prepare-reference')]

        args.extend(['--gtf', gtf.path])

        args.extend([
            '--star',
            '-p', self.cpus])

        args.extend([t.path for t in genome_fasta])

        args.append(self.output().prefix)

        return args

    def run(self):
        makedirs(self.output().path, exist_ok=True)
        return super().run()

    def output(self):
        return RsemReference(join(cfg.OUTPUT_DIR, cfg.REFERENCES, self.reference_id), self.taxon)

@no_retry
@requires(TrimSample, PrepareReference)
class AlignSample(ScheduledExternalProgramTask):
    """
    The output of the task is a pair of isoform and gene quantification results
    processed by STAR and RSEM.

    :attr strand_specific: Indicate if the RNA-Seq data is stranded
    """
    reference_id: str
    experiment_id: str
    sample_id: str

    # TODO: handle strand-specific reads
    strand_specific = luigi.BoolParameter(default=False, positional=False)

    scope = luigi.Parameter(default='genes', positional=False)

    cpus = 8
    memory = 32
    walltime = datetime.timedelta(days=1)

    # cleanup unused shared memory objects before and after the task is run
    # FIXME: move this into the configuration
    scheduler_extra_args = ['--gres=scratch:60G']

    def run(self):
        self.output().makedirs()
        return super().run()

    def _get_output_prefix(self):
        return join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, self.reference_id, self.experiment_id, self.sample_id)

    def program_args(self):
        args = [cfg.rsem_calculate_expression_bin]

        args.extend(['-p', self.cpus])

        args.extend([
            '--time',
            '--star',
            '--star-gzipped-read-file',
            '--no-bam-output'])

        if self.strand_specific:
            args.append('--strand-specific')

        runs, reference = self.input()

        forward_reads = []
        reverse_reads = []
        for run in runs:
            if len(run) == 2:
                forward_reads.append(run[0].path)
                reverse_reads.append(run[1].path)
            elif len(run) == 1:
                forward_reads.append(run[0].path)
            else:
                raise NotImplementedError("Only single or paired-end sequencing is supported.")

        if not forward_reads:
            raise ValueError('No forward reads found in the input runs. Please check the input data.')

        args.append(','.join(forward_reads))

        if reverse_reads:
            if len(forward_reads) != len(reverse_reads):
                raise ValueError('If reverse reads are provided, they must match the number of forward reads.')
            args.append('--paired-end')
            args.append(','.join(reverse_reads))

        # reference for alignments and quantifications
        args.append(reference.prefix)

        # output prefix
        args.append(self._get_output_prefix())

        return args

    def output(self):
        return luigi.LocalTarget(self._get_output_prefix() + f'.{self.scope}.results')

class AlignExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Align all the samples in a given experiment.

    The output is one sample alignment output per sample contained in the
    experiment.
    """
    experiment_id: str = luigi.Parameter()
    source: str = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'sra', 'arrayexpress', 'local'],
                                        positional=False)
    taxon: str = luigi.Parameter(positional=False)
    reference_id: str = luigi.Parameter(positional=False)
    scope: str = luigi.Parameter(default='genes', positional=False)

    def requires(self):
        return DownloadExperiment(self.experiment_id, source=self.source).requires().requires()

    def run(self):
        download_sample_tasks = next(DownloadExperiment(self.experiment_id, source=self.source).requires().run())
        yield [AlignSample(experiment_id=self.experiment_id,
                           sample_id=dst.sample_id,
                           source=self.source,
                           taxon=self.taxon,
                           reference_id=self.reference_id,
                           scope=self.scope)
               for dst in download_sample_tasks]

def write_sample_names_file(sample_names_file, trim_sample_dirs, qc_sample_dirs):
    os.makedirs(dirname(sample_names_file), exist_ok=True)
    with open(sample_names_file, 'w') as out:
        for sample_trim_dirs in trim_sample_dirs:
            for lane_trim in sample_trim_dirs:
                run_id = '___'.join(str(basename(lt.path).removesuffix('.fastq.gz'))
                                    for lt in lane_trim)
                sample_id = basename(dirname(dirname(lane_trim[0].path)))
                out.write(f'{run_id}\t{sample_id}_{run_id}\n')
        for lane_qc in flatten(qc_sample_dirs):
            run_id = basename(lane_qc.path).removesuffix('_fastqc.html')
            sample_id = basename(dirname(dirname(dirname(lane_qc.path))))
            out.write(f'{run_id}\t{sample_id}_{run_id}\n')

@no_retry
@requires(TrimExperiment, QualityControlExperiment, AlignExperiment)
class GenerateReportForExperiment(RerunnableTaskMixin, luigi.Task):
    """
    Generate a summary report for an experiment with MultiQC.

    The report include collected FastQC reports and RSEM/STAR outputs.
    """
    experiment_id: str
    reference_id: str

    def run(self):
        trim_sample_dirs, qc_sample_dirs, align_sample_dirs = self.input()
        search_dirs = set()
        search_dirs.update(dirname(out.path) for out in flatten(trim_sample_dirs))
        search_dirs.update(dirname(out.path) for out in flatten(qc_sample_dirs)),
        search_dirs.update(dirname(out.path) for out in flatten(align_sample_dirs))
        # we used to write the sample_names.tsv file inside the directory, but that is not working anymore since writing
        # MultiQC report now uses atomic write
        sample_names_file = join(cfg.OUTPUT_DIR, 'report', self.reference_id, self.experiment_id + '.sample_names.tsv')
        write_sample_names_file(sample_names_file, trim_sample_dirs, qc_sample_dirs)
        yield multiqc.GenerateReport(input_dirs=search_dirs,
                                     output_dir=dirname(self.output().path),
                                     replace_names=sample_names_file,
                                     force=self.rerun)

    def output(self):
        return luigi.LocalTarget(
            join(cfg.OUTPUT_DIR, 'report', self.reference_id, self.experiment_id, 'multiqc_report.html'))

@requires(AlignExperiment)
class CountExperiment(luigi.Task):
    """
    Combine the RSEM quantifications results from all the samples in a given
    experiment.

    The output is constituted of two matrices: genes counts and FPKM.
    """
    reference_id: str
    experiment_id: str
    scope: str

    resources = {'cpus': 1}

    def run(self):
        # FIXME: find a better way to obtain the sample identifier
        # Each DownloadSample-like tasks have a sample_id property! Use that!
        keys = [basename(f.path).replace(f'.{self.scope}.results', '') for f in self.input()]

        counts_buffer = pd.concat([pd.read_csv(f.path, sep='\t', index_col=0).expected_count for f in self.input()],
                                  keys=keys, axis=1).to_csv(sep='\t')
        fpkm_buffer = pd.concat([pd.read_csv(f.path, sep='\t', index_col=0).FPKM for f in self.input()], keys=keys,
                                axis=1).to_csv(sep='\t')

        with self.output()[0].open('w') as counts_out, self.output()[1].open('w') as fpkm_out:
            counts_out.write(counts_buffer)
            fpkm_out.write(fpkm_buffer)

    def output(self):
        destdir = join(cfg.OUTPUT_DIR, cfg.QUANTDIR, self.reference_id)
        return [luigi.LocalTarget(join(destdir, f'{self.experiment_id}_counts.{self.scope}')),
                luigi.LocalTarget(join(destdir, f'{self.experiment_id}_fpkm.{self.scope}'))]

class PrepareSingleCellReference(luigi.Task):
    reference_id = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(
            join(str(cfg.OUTPUT_DIR), str(cfg.SINGLE_CELL_REFERENCES), str(self.reference_id)))

@requires(DownloadSample)
class OrganizeSingleCellSample(luigi.Task):
    """Pre-populate a directory with FASTQs for a single-cell sample"""

    experiment_id: str
    sample_id: str

    def run(self):
        runs = flatten(self.input())
        with self.output().temporary_path() as output_dir:
            os.makedirs(output_dir)
            for lane, run in enumerate(runs):
                print(run)
                for f, read_type in zip(run.files, run.layout):
                    dest = join(output_dir, f'{self.sample_id}_S1_L{lane + 1:03}_{read_type}_001.fastq.gz')
                    if os.path.exists(dest):
                        unlink(dest)
                    link(f, dest)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, 'data-single-cell', self.experiment_id, self.sample_id))

@requires(OrganizeSingleCellSample, PrepareSingleCellReference)
class AlignSingleCellSample(DynamicWrapperTask):
    reference_id: str
    experiment_id: str
    sample_id: str

    chemistry: Optional[str] = luigi.OptionalParameter(default=None, positional=False)

    def run(self):
        fastqs_dir, transcriptome_dir = self.input()
        yield CellRangerCount(
            id=self.sample_id,
            transcriptome_dir=transcriptome_dir,
            fastqs_dir=fastqs_dir,
            output_dir=self.output().path,
            chemistry=self.chemistry,
            # TODO: add an avx feature on slurm
            scheduler_extra_args=['--constraint', 'thrd64', '--gres=scratch=300G']
        )

    def output(self):
        return luigi.LocalTarget(
            join(cfg.OUTPUT_DIR, cfg.QUANT_SINGLE_CELL_DIR, self.reference_id, self.experiment_id, self.sample_id))

@requires(DownloadExperiment)
class OrganizeSingleCellExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    experiment_id: str

    def run(self):
        download_sample_tasks = next(self.requires().run())
        yield [OrganizeSingleCellSample(experiment_id=self.experiment_id, sample_id=task.sample_id)
               for task in download_sample_tasks]

class AlignSingleCellExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    experiment_id: str = luigi.Parameter()
    source: str = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'sra', 'arrayexpress', 'local'],
                                        positional=False)
    reference_id: str = luigi.Parameter(positional=False)
    chemistry: Optional[str] = luigi.OptionalParameter(default=None, positional=False)

    def requires(self):
        return DownloadExperiment(self.experiment_id, source=self.source).requires().requires()

    def run(self):
        download_sample_tasks = next(DownloadExperiment(self.experiment_id, source=self.source).requires().run())
        yield [AlignSingleCellSample(experiment_id=self.experiment_id,
                                     sample_id=dst.sample_id,
                                     source=self.source,
                                     reference_id=self.reference_id,
                                     chemistry=self.chemistry)
               for dst in download_sample_tasks]

@requires(AlignSingleCellExperiment, TrimExperiment, QualityControlExperiment)
class GenerateReportForSingleCellExperiment(RerunnableTaskMixin, luigi.Task):
    """Generate a report for single-cell"""
    experiment_id: str
    reference_id: str

    def run(self):
        align_sample_dirs, trim_sample_dirs, qc_sample_dirs = self.input()
        search_dirs = set()
        search_dirs.update(dirname(out.path) for out in flatten(align_sample_dirs))
        search_dirs.update(dirname(out.path) for out in flatten(trim_sample_dirs))
        search_dirs.update(dirname(out.path) for out in flatten(qc_sample_dirs))

        # we used to write the sample_names.tsv file inside the directory, but that is not working anymore since writing
        # MultiQC report now uses atomic write
        sample_names_file = join(cfg.OUTPUT_DIR, 'report', self.reference_id, self.experiment_id + '.sample_names.tsv')
        write_sample_names_file(sample_names_file, trim_sample_dirs, qc_sample_dirs)
        yield multiqc.GenerateReport(input_dirs=search_dirs,
                                     output_dir=dirname(self.output().path),
                                     replace_names=sample_names_file,
                                     force=self.rerun)

    def output(self):
        return luigi.LocalTarget(
            join(cfg.OUTPUT_DIR, 'report', self.reference_id, self.experiment_id, 'multiqc_report.html'))

@no_retry
class SubmitBulkExperimentDataToGemma(RerunnableTaskMixin, GemmaCliTask):
    """
    Submit an experiment to Gemma.

    The metadata containing the taxon are fetched from Gemma REST API.

    This will trigger the whole pipeline.

    The output is a confirmation that the data is effectively in Gemma.
    """

    subcommand = 'rnaseqDataAdd'

    resources = {'submit_data_jobs': 1}

    def requires(self):
        return CountExperiment(self.experiment_id,
                               taxon=self.taxon,
                               reference_id=self.reference_id,
                               source='gemma',
                               scope='genes')

    def subcommand_args(self):
        count, fpkm = self.input()
        return ['-a', self.platform_short_name,
                '-count', count.path,
                '-rpkm', fpkm.path]

    def output(self):
        # there is also a log2cpm, but it is computed by Gemma
        return [GemmaDatasetQuantitationType(self.experiment_id, 'Counts', vector_type=GemmaDataVectorType.RAW),
                GemmaDatasetQuantitationType(self.experiment_id, 'RPKM', vector_type=GemmaDataVectorType.RAW)]

class SubmitSingleCellExperimentDataToGemma(GemmaCliTask):
    subcommand = 'loadSingleCellData'

    resources = {'submit_data_jobs': 1}

    def requires(self):
        return AlignSingleCellExperiment(experiment_id=self.experiment_id,
                                         reference_id=self.reference_id,
                                         source='gemma')

    def subcommand_args(self):
        return ['-a', self.platform_short_name,
                '--data-path', self._data_dir,
                '--data-type', 'MEX',
                '--quantitation-type-recomputed-from-raw-data',
                '--preferred-quantitation-type',
                # never filter 10x MEX data (this prevents detection of unfiltered data)
                '--mex-no-10x-filter',
                # TODO: add sequencing metadata
                # FIXME: add --replace
                ]

    def run(self):
        with tempfile.TemporaryDirectory() as self._data_dir:
            for sample_dir in self.input():
                new_sample_dir = join(self._data_dir, basename(sample_dir.path))
                makedirs(new_sample_dir)
                symlink(join(sample_dir.path, 'outs/filtered_feature_bc_matrix/barcodes.tsv.gz'),
                        join(new_sample_dir, 'barcodes.tsv.gz'))
                symlink(join(sample_dir.path, 'outs/filtered_feature_bc_matrix/features.tsv.gz'),
                        join(new_sample_dir, 'features.tsv.gz'))
                symlink(join(sample_dir.path, 'outs/filtered_feature_bc_matrix/matrix.mtx.gz'),
                        join(new_sample_dir, 'matrix.mtx.gz'))
            super().run()

    def output(self):
        return GemmaDatasetQuantitationType(self.experiment_id, '10x MEX', vector_type=GemmaDataVectorType.SINGLE_CELL)

class SubmitExperimentDataToGemma(GemmaTaskMixin, WrapperTask):
    def requires(self):
        if self.assay_type == GemmaAssayType.BULK_RNA_SEQ:
            return SubmitBulkExperimentDataToGemma(experiment_id=self.experiment_id)
        elif self.assay_type == GemmaAssayType.SINGLE_CELL_RNA_SEQ:
            return SubmitSingleCellExperimentDataToGemma(experiment_id=self.experiment_id)
        else:
            raise NotImplementedError('Loading ' + self.assay_type + ' data to Gemma is not implemented.')

class SubmitExperimentBatchInfoToGemma(RerunnableTaskMixin, GemmaCliTask):
    """
    Submit the batch information of an experiment to Gemma.
    """

    subcommand = 'fillBatchInfo'

    resources = {'submit_batch_info_jobs': 1}

    ignored_samples = luigi.ListParameter(default=[])

    def requires(self):
        # TODO: Have a generic strategy for extracting batch info that would
        # work for all sources
        if self.external_database == 'GEO':
            return ExtractGeoSeriesBatchInfo(self.accession, metadata=dict(experiment_id=self.experiment_id),
                                             ignored_samples=self.ignored_samples)
        elif self.external_database == 'SRA':
            return ExtractSraProjectBatchInfo(self.accession, metadata=dict(experiment_id=self.experiment_id),
                                              ignored_samples=self.ignored_samples)
        else:
            raise NotImplementedError(
                'Extracting batch information from {} is not supported.'.format(self.external_database))

    def output(self):
        return GemmaDatasetHasBatch(self.experiment_id)

class SubmitExperimentReportToGemma(RerunnableTaskMixin, GemmaCliTask):
    """
    Submit an experiment QC report to Gemma.
    """
    experiment_id: str = luigi.Parameter()

    subcommand = 'addMetadataFile'

    def requires(self):
        if self.assay_type == GemmaAssayType.BULK_RNA_SEQ:
            return GenerateReportForExperiment(experiment_id=self.experiment_id,
                                               taxon=self.taxon,
                                               reference_id=self.reference_id,
                                               source='gemma',
                                               rerun=self.rerun)
        elif self.assay_type == GemmaAssayType.SINGLE_CELL_RNA_SEQ:
            return GenerateReportForSingleCellExperiment(experiment_id=self.experiment_id,
                                                         reference_id=self.reference_id,
                                                         source='gemma',
                                                         rerun=self.rerun)
        else:
            raise NotImplementedError('Cannot generate report for a ' + self.assay_type + ' experiment.')

    def subcommand_args(self):
        return ['-e', self.experiment_id, '--file-type', 'RNASEQ_PIPELINE_REPORT', '--changelog-entry',
                'Adding MultiQC report generated by the RNA-Seq pipeline', self.input().path]

    def output(self):
        return luigi.LocalTarget(
            join(gemma_cfg.appdata_dir, 'metadata', self.experiment_id, 'MultiQCReports/multiqc_report.html'))

@requires(SubmitExperimentDataToGemma, SubmitExperimentBatchInfoToGemma, SubmitExperimentReportToGemma)
class SubmitExperimentToGemma(TaskWithOutputMixin, WrapperTask):
    """
    Submit an experiment data, QC reports, and batch information to Gemma.
    """
    experiment_id: str

    priority = luigi.IntParameter(default=100, positional=False, significant=False)

    def _targets_to_remove(self):
        outs = []
        # original data
        # TODO: check if data is local, we don't want to delete that
        download_task = DownloadExperiment(self.experiment_id, source='gemma')
        outs.extend(flatten_output(download_task))
        # any data resulting from trimming raw reads
        trim_task = TrimExperiment(self.experiment_id, source='gemma')
        outs.extend(flatten_output(trim_task))
        # reorganized data for the scRNA-Seq pipeline
        organize_task = OrganizeSingleCellExperiment(self.experiment_id, source='gemma')
        outs.extend(flatten_output(organize_task))
        return outs

    def on_success(self):
        # report success to curators
        if cfg.SLACK_WEBHOOK_URL is not None:
            payload = {
                'text': '<https://gemma.msl.ubc.ca/expressionExperiment/showExpressionExperiment.html?shortName={0}|{0}> data and batch information have been successfully submitted to Gemma.'.format(
                    self.experiment_id)}
            requests.post(cfg.SLACK_WEBHOOK_URL, json=payload)
        return super().on_success()

    def run(self):
        # cleanup download data
        remove_task_output(DownloadExperiment(self.experiment_id, source='gemma'))
        remove_task_output(TrimExperiment(self.experiment_id, source='gemma'))

    def complete(self):
        """
        We consider a submission completed when data and batch information have
        been successfully submitted to Gemma and any remaining downloaded and
        trimmed data has been removed.

        Ideally we would delete the data earlier, but it's necessary for both
        quantification and batch info extraction.
        """
        return super().complete() and all(not out.exists() for out in self._targets_to_remove())

class SubmitExperimentsFromDataFrameMixin:
    ignore_priority = luigi.BoolParameter(positional=False, significant=False,
                                          description='Ignore the priority column and inherit the priority of the this task. Rows with zero priority are nonetheless ignored.')

    def requires(self):
        df = self._retrieve_dataframe()
        # using None, the worker will inherit the priority from this task for all its dependencies
        try:
            return [SubmitExperimentToGemma(experiment_id=row.experiment_id,
                                            priority=100 if self.ignore_priority else row.get('priority',
                                                                                              100))
                    for _, row in df.iterrows() if row.get('priority', 1) > 0]
        except AttributeError as e:
            raise Exception(f'Failed to read experiments from {self._filename()}, is it valid?') from e

    def _filename(self):
        raise NotImplementedError

    def _retrieve_dataframe(self):
        raise NotImplementedError

class SubmitExperimentsFromFileToGemma(SubmitExperimentsFromDataFrameMixin, TaskWithOutputMixin, WrapperTask):
    input_file: str = luigi.Parameter()

    def _filename(self):
        return self.input_file

    def _retrieve_dataframe(self):
        return pd.read_csv(self.input_file, sep='\t', converters={'priority': lambda x: 0 if x == '' else int(x)})

class SubmitExperimentsFromGoogleSpreadsheetToGemma(SubmitExperimentsFromDataFrameMixin, WrapperTask):
    spreadsheet_id: str = luigi.Parameter(
        description='Spreadsheet ID in Google Sheets (lookup {spreadsheetId} in https://docs.google.com/spreadsheets/d/{spreadsheetId}/edit)')
    sheet_name: str = luigi.Parameter(description='Name of the spreadsheet in the document')

    def _filename(self):
        return 'https://docs.google.com/spreadsheets/d/' + self.spreadsheet_id

    # TODO: use the spreadsheet revision ID
    # For now, all that does is distinguishing spreadsheet tasks which might
    # refer to different revisions, which in turn allows newly added tasks to
    # be executed
    revision_id = luigi.Parameter(default=str(uuid.uuid4()),
                                  description='Revision ID of the spreadsheet (not yet supported, but will default to the latest)')

    def _retrieve_dataframe(self):
        from .gsheet import retrieve_spreadsheet
        return retrieve_spreadsheet(self.spreadsheet_id, self.sheet_name)

class ReorganizeSplitExperiment(GemmaTaskMixin):
    """Reorganize a Gemma dataset that was split."""

    num_splits: int = luigi.IntParameter()

    def run(self):
        dirs_to_relocate = [
            join(cfg.OUTPUT_DIR, 'data-trimmed'),
            join(cfg.OUTPUT_DIR, cfg.DATAQCDIR),
            join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, '*'),
            join(cfg.OUTPUT_DIR, cfg.QUANTDIR, '*'),
            join(cfg.OUTPUT_DIR, cfg.QUANT_SINGLE_CELL_DIR, '*')
        ]

        for split_id in range(self.num_splits):
            split_id = self.experiment_id + '.' + str(split_id + 1)
            logger.info('Reorganizing data for %s.', split_id)
            for sample in gemma_api.samples(split_id):
                sample_id = sample['accession']['accession']
                for d in dirs_to_relocate:
                    for sample_file in iglob(join(d, self.experiment_id, sample_id)):
                        new_sample_file = join(dirname(dirname(sample_file)), split_id, sample_id)
                        logger.info('Moving %s to %s.', sample_file, new_sample_file)
                        os.makedirs(dirname(new_sample_file), exist_ok=True)
                        shutil.move(sample_file, new_sample_file)
