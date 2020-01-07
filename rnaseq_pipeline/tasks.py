import datetime
from glob import glob
import os
from os.path import join
import logging

import pandas as pd
import requests
import luigi
import luigi.task
from luigi.contrib.external_program import ExternalProgramTask
from luigi.util import requires
from bioluigi.tasks import fastqc, multiqc
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask
import yaml

from .config import rnaseq_pipeline
from .cwl_utils import gen_workflow
from .utils import WrapperTask, DynamicWrapperTask, no_retry, GemmaTask
from .sources.geo import DownloadGeoSample, DownloadGeoSeries, ExtractGeoSeriesBatchInfo
from .sources.sra import DownloadSraProject, DownloadSraExperiment
from .sources.local import DownloadLocalSample, DownloadLocalExperiment
from .sources.gemma import DownloadGemmaExperiment
from .sources.arrayexpress import DownloadArrayExpressSample, DownloadArrayExpressExperiment
from .targets import GemmaDatasetHasPlatform, GemmaDatasetHasBatchInfo, RsemReference

logger = logging.getLogger('luigi-interface')

cfg = rnaseq_pipeline()

class DownloadSample(WrapperTask):
    """
    This is a generic task for downloading an individual sample in an
    experiment.

    Note that the 'gemma' source does not provide individual samples.
    """
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    source = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'arrayexpress', 'local', 'sra'], positional=False)

    def requires(self):
        if self.source in ['geo', 'gemma']:
            return DownloadGeoSample(self.sample_id)
        elif self.source == 'sra':
            return DownloadSraExperiment(self.sample_id)
        elif self.source == 'arrayexpress':
            return DownloadArrayExpressSample(self.experiment_id, self.sample_id)
        elif self.source == 'local':
            return DownloadLocalSample(self.experiment_id, self.sample_id)
        else:
            raise ValueError('Unknown source for sample: {}.'.format(self.source))

class DownloadExperiment(WrapperTask):
    """
    This is a generic task that detects which kind of experiment is intended to
    be downloaded so that downstream tasks can process regardless of the data
    source.

    :source: Indicate the origin of the experiment, otherwise it will be
    inferred from the :experiment_id: parameter.
    """
    experiment_id = luigi.Parameter()

    source = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'sra', 'arrayexpress', 'local'], positional=False)

    def requires(self):
        if self.source == 'gemma':
            return DownloadGemmaExperiment(self.experiment_id)
        elif self.source == 'geo':
            return DownloadGeoSeries(self.experiment_id)
        elif source == 'sra':
            return DownloadSraProject(self.experiment_id)
        elif self.source == 'arrayexpress':
            return DownloadArrayExpressExperiment(self.experiment_id)
        elif self.source == 'local':
            return DownloadLocalExperiment(self.experiment_id)
        else:
            raise ValueError('Unknown download source for experiment: {}.')

@no_retry
@requires(DownloadSample)
class QualityControlSample(luigi.Task):
    """
    Perform post-download quality control on the FASTQs.
    """

    def run(self):
        for fastq_in, report_out in zip(self.input(), self.output()):
            report_out.makedirs()
            yield fastqc.GenerateReport(fastq_in.path, os.path.dirname(report_out.path))

    def output(self):
        destdir = join(cfg.OUTPUT_DIR, cfg.DATAQCDIR, self.experiment_id, self.sample_id)
        return [luigi.LocalTarget(join(destdir, fastqc.GenerateReport.gen_report_basename(t.path)))
                for t in self.input()]

@requires(DownloadExperiment)
class QualityControlExperiment(DynamicWrapperTask):
    """
    Quality control all the samples in a given experiment.
    """
    def run(self):
        # the amout of requires() here is ridiculous
        download_sample_tasks = self.requires().requires().requires()
        yield [QualityControlSample(self.experiment_id,
                                    dst.sample_id,
                                    source=self.source)
               for dst in download_sample_tasks if len(dst.output()) > 0]

@no_retry
class PrepareReference(ScheduledExternalProgramTask):
    """
    Prepare a STAR/RSEM reference.

    :param taxon: Taxon
    :param reference_id: Reference annotation build to use (i.e. ensembl98, hg38_ncbi)
    """
    taxon = luigi.Parameter(default='human')
    reference_id = luigi.Parameter(default='hg38_ncbi')

    walltime = datetime.timedelta(hours=12)
    cpus = 16
    memory = 32

    def input(self):
        genome_dir = join(cfg.GENOMES, self.reference_id)
        gtf_files = glob(join(genome_dir, '*.gtf'))
        fasta_files = glob(join(genome_dir, '*.fa'))
        if len(gtf_files) != 1:
            raise ValueError('Only one GTF file is expected in {}.'.format(genome_dir))
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

        args.append(self.output().path)

        return args

    def output(self):
        return RsemReference(join(cfg.REFERENCES, self.reference_id, '{}_0'.format(self.taxon)))

@no_retry
@requires(DownloadSample, QualityControlSample, PrepareReference)
class AlignSample(ScheduledExternalProgramTask):
    """
    The output of the task is a pair of isoform and gene quantification results
    processed by STAR and RSEM.

    :attr ignore_mate: Ignore the second mate in the case of paired reads
    :attr strand_specific: Indicate if the RNA-Seq data is stranded
    """
    ignore_mate = luigi.BoolParameter(default=False, positional=False)

    # TODO: handle strand-specific reads
    strand_specific = luigi.BoolParameter(default=False, positional=False)

    walltime = datetime.timedelta(days=1)
    cpus = 8
    memory = 32

    def run(self):
        self.output().makedirs()
        return super(AlignSample, self).run()

    def program_args(self):
        args = [join(cfg.RSEM_DIR, 'rsem-calculate-expression'), '-p', self.cpus]

        args.extend([
            '--time',
            '--star',
            '--star-gzipped-read-file',
            '--no-bam-output'])

        if self.strand_specific:
            args.append('--strand-specific')

        sample_run, _, reference = self.input()

        fastqs = [mate.path for mate in sample_run]

        if len(fastqs) == 1:
            args.append(fastqs[0])
        elif len(fastqs) == 2 and self.ignore_mate:
            logger.info('Mate is ignored for %s.', repr(self))
            args.append(fastqs[0])
        elif len(fastqs) == 2:
            args.append('--paired-end')
            args.extend(fastqs)
        else:
            raise NotImplementedError('More than two input FASTQs are not supported.')

        # reference for alignments and quantifications
        args.append(join(reference.path))

        # output prefix
        args.append(join(os.path.dirname(self.output().path), self.sample_id))

        return args

    def output(self):
        destdir = join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, self.reference_id, self.experiment_id)
        return luigi.LocalTarget(join(destdir, '{}.genes.results'.format(self.sample_id)))

@requires(DownloadExperiment)
class AlignExperiment(DynamicWrapperTask):
    """
    Align all the samples in a given experiment.

    The output is one sample alignment output per sample contained in the
    experiment.
    """
    taxon = luigi.Parameter(default='human', positional=False)
    reference_id = luigi.Parameter(default='hg38_ncbi', positional=False)

    def run(self):
        download_sample_tasks = self.requires().requires().requires()
        yield [AlignSample(self.experiment_id,
                           dst.sample_id,
                           source=self.source,
                           taxon=self.taxon,
                           reference_id=self.reference_id)
               for dst in download_sample_tasks if len(dst.output()) > 0]

@no_retry
@requires(QualityControlExperiment, AlignExperiment)
class GenerateReportForExperiment(luigi.Task):
    """
    Generate a summary report for an experiment with MultiQC.

    The report include collected FastQC reports and RSEM/STAR outputs.
    """

    def run(self):
        search_dirs = [
            join(cfg.OUTPUT_DIR, cfg.DATAQCDIR, self.experiment_id),
            join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, self.reference_id, self.experiment_id)]
        self.output().makedirs()
        yield multiqc.GenerateReport(search_dirs, os.path.dirname(self.output().path))

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, 'report', self.reference_id, self.experiment_id, 'multiqc_report.html'))

@requires(AlignExperiment)
class CountExperiment(luigi.Task):
    """
    Combine the RSEM quantifications results from all the samples in a given
    experiment.

    The output is constituted of two matrices: genes counts and FPKM.
    """
    resources = {'cpus': 1}

    def run(self):
        # FIXME: find a better way to obtain the sample identifier
        keys = [os.path.basename(gene.path).replace('.genes.results', '') for gene in self.input()]
        counts_df = pd.concat([pd.read_csv(gene.path, sep='\t', index_col=0).expected_count for gene in self.input()], keys=keys, axis=1)
        fpkm_df = pd.concat([pd.read_csv(gene.path, sep='\t', index_col=0).FPKM for gene in self.input()], keys=keys, axis=1)

        with self.output()[0].open('w') as counts_out, self.output()[1].open('w') as fpkm_out:
            counts_df.to_csv(counts_out, sep='\t')
            fpkm_df.to_csv(fpkm_out, sep='\t')

    def output(self):
        destdir = join(cfg.OUTPUT_DIR, cfg.QUANTDIR, self.reference_id)
        return [luigi.LocalTarget(join(destdir, '{}_counts.genes'.format(self.experiment_id))),
                luigi.LocalTarget(join(destdir, '{}_fpkm.genes'.format(self.experiment_id)))]

@requires(CountExperiment)
class GenerateWorkflowMetadataForExperiment(luigi.Task):
    def run(self):
        with self.output().open('w') as f:
            yaml.dump(gen_workflow(self.requires()), f)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, 'workflow', '{}.cwl'.format(self.experiment_id)))

class SubmitBatchInfoToGemma(GemmaTask):
    """
    Submit the batch information of an experiment to Gemma.
    """

    subcommand = 'fillBatchInfo'

    def requires(self):
        dataset_info = self.get_dataset_info()

        # TODO: Have a generic strategy for extracting batch info that would
        # work for all sources
        if dataset_info['externalDatabase'] == 'GEO':
            return ExtractGeoSeriesBatchInfo(dataset_info['accession'])
        else:
            raise NotImplementedError('Extracting batch information from {} is not implemented.'.format(dataset_info['externalDatabase']))

    def subcommand_args(self):
        return ['--force', 'yes', '-f', self.input().path]

    def output(self):
        return GemmaDatasetHasBatchInfo(self.experiment_id)

@no_retry
class SubmitExperimentToGemma(GemmaTask):
    """
    Submit an experiment to Gemma.

    The metadata containing the taxon are fetched from Gemma REST API.

    This will trigger the whole pipeline.

    The output is a confirmation that the data is effectively in Gemma.
    """

    subcommand = 'rnaseqDataAdd'

    resubmit = luigi.BoolParameter(default=False, positional=False, significant=False)
    priority = luigi.IntParameter(default=0, positional=False, significant=False)

    def on_success(self):
        """
        Notify curators that the dataset is now available on Gemma.
        """
        if cfg.SLACK_WEBHOOK_URL is not None:
            payload = {'text': '<https://gemma.msl.ubc.ca/expressionExperiment/showExpressionExperiment.html?shortName={0}|{0}> RNA-Seq data has been successfully submitted to Gemma.'.format(self.experiment_id)}
            requests.post(cfg.SLACK_WEBHOOK_URL, json=payload)
        return super(SubmitExperimentToGemma, self).on_success()

    def requires(self):
        dataset_info = self.get_dataset_info()

        taxon = dataset_info['taxon']

        yield CountExperiment(self.experiment_id,
                              taxon=taxon,
                              reference_id=self.get_reference_id_for_taxon(taxon),
                              source='gemma')

        # FIXME: this does not always trigger the dependencies
        yield GenerateReportForExperiment(self.experiment_id,
                                          taxon=taxon,
                                          reference_id=self.get_reference_id_for_taxon(taxon),
                                          source='gemma')

    def subcommand_args(self):
        (count, fpkm), _ = self.input()
        # TODO: submit the batch information and the MultiQC report
        return ['-a', self.get_platform_short_name(),
                '-count', count.path,
                '-rpkm', fpkm.path]

    def output(self):
        return GemmaDatasetHasPlatform(self.experiment_id, self.get_platform_short_name())

    def complete(self):
        return (not self.resubmit) and super(SubmitExperimentToGemma, self).complete()

class SubmitExperimentsFromFileToGemma(WrapperTask):
    input_file = luigi.Parameter()
    def requires(self):
        df = pd.read_csv(self.input_file, sep='\t', converters={'priority': lambda x: 0 if x == '' else int(x)})
        return [[SubmitExperimentToGemma(row.experiment_id, priority=row.get('priority', 0)),
                 SubmitBatchInfoToGemma(row.experiment_id)]
                for _, row in df.iterrows()]
