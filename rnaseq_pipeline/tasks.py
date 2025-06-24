import datetime
import logging
import os
import tempfile
import uuid
from glob import glob
from os.path import join, dirname

import luigi
import luigi.task
import pandas as pd
import requests
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask
from bioluigi.tasks import fastqc, multiqc
from bioluigi.tasks.cellranger import CellRangerCount
from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, TaskWithOutputMixin, DynamicWrapperTask
from luigi.task import flatten_output, WrapperTask
from luigi.util import requires

from .config import rnaseq_pipeline
from .gemma import GemmaCliTask, gemma
from .sources.arrayexpress import DownloadArrayExpressSample, DownloadArrayExpressExperiment
from .sources.gemma import DownloadGemmaExperiment
from .sources.geo import DownloadGeoSample, DownloadGeoSeries, ExtractGeoSeriesBatchInfo
from .sources.local import DownloadLocalSample, DownloadLocalExperiment
from .sources.sra import DownloadSraProject, DownloadSraExperiment, ExtractSraProjectBatchInfo
from .targets import GemmaDatasetPlatform, GemmaDatasetHasBatch, RsemReference
from .utils import no_retry, RerunnableTaskMixin, remove_task_output

logger = logging.getLogger(__name__)

cfg = rnaseq_pipeline()
gemma_cfg = gemma()

class DownloadSample(TaskWithOutputMixin, WrapperTask):
    """
    This is a generic task for downloading an individual sample in an
    experiment.

    Note that the 'gemma' source does not provide individual samples.

    The output of this task is a list of tuple of FASTQ files organized as follows:
    - for single-end reads, [(R1)]
    - for paired-end reads, [(R1, R2)]
    - for paired-end reads with an index file, [(I1, R1, R2)]
    - for paired-end reads with two index files, [(I1, I2, R1, R2)]
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

class DownloadExperiment(TaskWithOutputMixin, WrapperTask):
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
            return DownloadGemmaExperiment(self.experiment_id)
        elif self.source == 'geo':
            return DownloadGeoSeries(self.experiment_id)
        elif self.source == 'sra':
            return DownloadSraProject(self.experiment_id)
        elif self.source == 'arrayexpress':
            return DownloadArrayExpressExperiment(self.experiment_id)
        elif self.source == 'local':
            return DownloadLocalExperiment(self.experiment_id)
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
        destdir = join(cfg.OUTPUT_DIR, 'data-trimmed', self.experiment_id, self.sample_id)
        os.makedirs(destdir, exist_ok=True)
        download_sample_task = self.requires()
        platform = download_sample_task.requires().platform
        if len(self.input()) == 1:
            r1, = self.input()
            yield platform.get_trim_single_end_reads_task(
                r1.path,
                join(destdir, os.path.basename(r1.path)),
                minimum_length=self.minimum_length,
                report_file=join(destdir, os.path.basename(r1.path) + '.cutadapt.json'),
                cpus=4)
        elif len(self.input()) == 2:
            r1, r2 = self.input()
            r1, r2 = self.input()
            if self.ignore_mate == 'forward':
                logger.info('Forward mate is ignored for %s.', repr(self))
                yield platform.get_trim_single_end_reads_task(
                    r2.path,
                    join(destdir, os.path.basename(r2.path)),
                    minimum_length=self.minimum_length,
                    report_file=join(destdir, os.path.basename(r2.path) + '.cutadapt.json'),
                    cpus=4)
            elif self.ignore_mate == 'reverse':
                logger.info('Reverse mate is ignored for %s.', repr(self))
                yield platform.get_trim_single_end_reads_task(
                    r1.path,
                    join(destdir, os.path.basename(r1.path)),
                    minimum_length=self.minimum_length,
                    report_file=join(destdir, os.path.basename(r1.path) + '.cutadapt.json'),
                    cpus=4)
            else:
                yield platform.get_trim_paired_reads_task(
                    r1.path, r2.path,
                    join(destdir, os.path.basename(r1.path)),
                    join(destdir, os.path.basename(r2.path)),
                    minimum_length=self.minimum_length,
                    report_file=join(destdir,
                                     os.path.basename(r1.path) + '_' + os.path.basename(r2.path) + '.cutadapt.json'),
                    cpus=4)
        else:
            raise NotImplementedError('Trimming more than two mates is not supported.')

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
        destdir = join(cfg.OUTPUT_DIR, cfg.DATAQCDIR, self.experiment_id, self.sample_id)
        os.makedirs(destdir, exist_ok=True)
        yield [fastqc.GenerateReport(fastq_in.path, output_dir=destdir, temp_dir=tempfile.gettempdir()) for fastq_in in
               self.input()]

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
        os.makedirs(self.output().path, exist_ok=True)
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
        args = ['scripts/rsem-calculate-expression-wrapper', join(cfg.RSEM_DIR, 'rsem-calculate-expression'), '-p',
                self.cpus]

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
            if 'R1' in run.layout and 'R2' in run.layout:
                forward_reads.append(run.files[run.layout.index('R1')])
                reverse_reads.append(run.files[run.layout.index('R2')])
            elif 'R1' in run.layout:
                forward_reads.append(run.files[run.layout.index('R1')])
            elif 'R2' in run.layout:
                logging.warning('Found an unpaired reverse read in run %s, will treat it as single-end.', run.run_id)
                forward_reads.append(run.files[run.layout.index('R1')])
            else:
                logger.warning("Unsupported layout for run %s, it will be ignored.", run.run_id)

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
        fastqc_dir = join(cfg.OUTPUT_DIR, cfg.DATAQCDIR, self.experiment_id)
        search_dirs = [
            join(cfg.OUTPUT_DIR, 'data-trimmed', self.experiment_id),
            fastqc_dir,
            join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, self.reference_id, self.experiment_id)]
        self.output().makedirs()

        # generate sample mapping for FastQC files
        fastqc_suffix = '_fastqc.zip'
        sample_names_file = join(cfg.OUTPUT_DIR, 'report', self.reference_id, self.experiment_id, 'sample_names.tsv')
        with open(sample_names_file, 'w') as out:
            for root, dirs, files in os.walk(fastqc_dir):
                for f in files:
                    if f.endswith(fastqc_suffix):
                        fastqc_sample_id = f[:-len(fastqc_suffix)]
                        sample_id = os.path.basename(root)
                        # To avoid sample name clashes for paired-read
                        # sequencing, we need to add a suffix to the sample ID
                        # In single-end sequencing, fastq-dump does not
                        # produces _1, _2 suffixes, so the FastQC metrics will
                        # appear in the same row
                        if fastqc_sample_id.endswith('_1'):
                            sample_id += '_1'
                        elif fastqc_sample_id.endswith('_2'):
                            sample_id += '_2'
                        out.write(f'{fastqc_sample_id}\t{sample_id}\n')

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
        keys = [os.path.basename(f.path).replace(f'.{self.scope}.results', '') for f in self.input()]

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
        runs = self.input()
        os.makedirs(self.output().path)
        for lane, run in enumerate(runs):
            for f, read_type in zip(run.files, run.layout):
                dest = join(self.output().path, f'{self.sample_id}_S1_L{lane + 1:03}_{read_type}_001.fastq.gz')
                if os.path.exists(dest):
                    os.unlink(dest)
                os.link(f, dest)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, 'data-single-cell', self.experiment_id, self.sample_id))

@requires(OrganizeSingleCellSample, PrepareSingleCellReference)
class AlignSingleCellSample(DynamicWrapperTask):
    experiment_id: str
    sample_id: str

    def run(self):
        fastqs_dir, transcriptome_dir = self.input()
        yield CellRangerCount(
            id=self.sample_id,
            transcriptome_dir=transcriptome_dir,
            fastqs_dir=fastqs_dir,
            output_dir=self.output().path,
            # TODO: add an avx feature on slurm
            scheduler_extra_args=['--constraint', 'thrd64']
    )

    def output(self):
        return luigi.LocalTarget(
            join(cfg.OUTPUT_DIR, 'quantified-single-cell', self.reference_id, self.experiment_id, self.sample_id))

class AlignSingleCellExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    experiment_id: str = luigi.Parameter()
    source: str = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'sra', 'arrayexpress', 'local'],
                                        positional=False)
    reference_id: str = luigi.Parameter(positional=False)

    def requires(self):
        return DownloadExperiment(self.experiment_id, source=self.source).requires().requires()

    def run(self):
        download_sample_tasks = next(DownloadExperiment(self.experiment_id, source=self.source).requires().run())
        yield [AlignSingleCellSample(experiment_id=self.experiment_id,
                                     sample_id=dst.sample_id,
                                     source=self.source,
                                     reference_id=self.reference_id)
               for dst in download_sample_tasks]

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

@no_retry
class SubmitExperimentDataToGemma(RerunnableTaskMixin, GemmaCliTask):
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
        return GemmaDatasetPlatform(self.experiment_id, self.platform_short_name)

class SubmitExperimentReportToGemma(RerunnableTaskMixin, GemmaCliTask):
    """
    Submit an experiment QC report to Gemma.
    """
    experiment_id: str = luigi.Parameter()

    subcommand = 'addMetadataFile'

    def requires(self):
        return GenerateReportForExperiment(self.experiment_id,
                                           taxon=self.taxon,
                                           reference_id=self.reference_id,
                                           source='gemma',
                                           rerun=self.rerun)

    def subcommand_args(self):
        return ['-e', self.experiment_id, '--file-type', 'MULTIQC_REPORT', '--changelog-entry',
                'Adding MultiQC report generated by the RNA-Seq pipeline', self.input().path]

    def output(self):
        return luigi.LocalTarget(
            join(gemma_cfg.appdata_dir, 'metadata', self.experiment_id, 'MultiQCReports/multiqc_report.html'))

class SubmitSingleCellExperimentDataToGemma(RerunnableTaskMixin, GemmaCliTask):
    experiment_id: str = luigi.Parameter()
    subcommand = 'loadSingleCellData'

    def requires(self):
        return AlignSingleCellExperiment(experiment_id=self.experiment_id,
                                         reference_id=self.single_cell_reference_id(),
                                         source='gemma')

    def subcommand_args(self):
        return ['-e', self.experiment_id, '-a', self.platform_short_name,
                '--data-path', self.input().path,
                '--quantitation-type-recomputed-from-raw-data',
                '--preferred-quantitation-type',
                # TODO: add sequencing metadata
                # FIXME: add --replace
                ]

@requires(SubmitExperimentDataToGemma, SubmitExperimentBatchInfoToGemma, SubmitExperimentReportToGemma)
class SubmitExperimentToGemma(TaskWithOutputMixin, WrapperTask):
    """
    Submit an experiment data, QC reports, and batch information to Gemma.

    TODO: add QC report submission
    """
    experiment_id: str

    # Makes it so that we recheck if the task is complete after 20 minutes.
    # This is because Gemma Web API is caching reply for 1200 seconds, so the
    # batch factor will not appear until until the query is evicted.
    # See https://github.com/PavlidisLab/rnaseq-pipeline/issues/76 for details
    retry_count = 1
    retry_delay = 1200

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
            return [SubmitExperimentToGemma(row.experiment_id,
                                            priority=100 if self.ignore_priority else row.get('priority', 100),
                                            rerun=row.get('data') == 'resubmit')
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
