import datetime
import gzip
import os
from os.path import join
import logging

import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import luigi
import luigi.task
from luigi.contrib.external_program import ExternalProgramTask
from bioluigi.tasks import fastqc
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask

from .config import rnaseq_pipeline
from .utils import WrapperTask
from .sources.geo import DownloadGeoSample, DownloadGeoSeries, ExtractGeoSeriesInfo
from .sources.local import DownloadLocalSample, DownloadLocalExperiment
from .sources.gemma import DownloadGemmaExperiment
from .sources.arrayexpress import DownloadArrayExpressSample, DownloadArrayExpressExperiment
from .targets import GemmaDatasetHasPlatform

EXPERIMENT_SOURCES = ['gemma', 'geo', 'arrayexpress', 'local']
SAMPLE_SOURCES = ['geo', 'arrayexpress', 'local']

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

    source = luigi.ChoiceParameter(default='local', choices=SAMPLE_SOURCES, positional=False)

    def requires(self):
        if self.source == 'geo':
            return DownloadGeoSample(self.sample_id)
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

    source = luigi.ChoiceParameter(default='local', choices=EXPERIMENT_SOURCES, positional=False)

    def requires(self):
        if self.source == 'gemma':
            return DownloadGemmaExperiment(self.experiment_id)
        elif self.source == 'geo':
            return DownloadGeoSeries(self.experiment_id)
        elif self.source == 'arrayexpress':
            return DownloadArrayExpressExperiment(self.experiment_id)
        elif self.source == 'local':
            return DownloadLocalExperiment(self.experiment_id)
        else:
            raise ValueError('Unknown download source for experiment: {}.')

class QualityControlSample(luigi.Task):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    source = luigi.ChoiceParameter(default='local', choices=SAMPLE_SOURCES, positional=False)

    def requires(self):
        return DownloadSample(self.experiment_id, self.sample_id, source=self.source)

    def run(self):
        for fastq_in, report_out in zip(self.input(), self.output()):
            report_out.makedirs()
            yield fastqc.GenerateReport(fastq_in.path, os.path.dirname(report_out.path),
                                        scheduler_extra_args=['--partition', 'Cargo'])

    def output(self):
        destdir = join(cfg.OUTPUT_DIR, cfg.DATAQCDIR, self.experiment_id, self.sample_id)
        return [luigi.LocalTarget(join(destdir, fastqc.GenerateReport.gen_report_basename(t.path)))
                for t in self.input()]

class PrepareReference(ScheduledExternalProgramTask):
    """
    Prepare a STAR/RSEM reference.
    """
    taxon = luigi.Parameter(default='human')
    genome_build = luigi.Parameter(default='hg38')
    reference_build = luigi.Parameter(default='ncbi')

    scheduler_extra_args = ['--partition', 'Cargo']
    walltime = datetime.timedelta(hours=12)
    cpus = 16
    memory = 32

    def program_args(self):
        return [join(cfg.RSEM_DIR, 'rsem-prepare-reference'),
                join(cfg.ASSEMBLIES, '{}_{}'.format(self.genome_build, self.reference_build), '*.gtf'),
                '--star',
                '--star-path', cfg.STAR_PATH,
                '-p', self.cpus,
                join(cfg.ASSEMBLIES, '{}_{}'.format(self.genome_build, self.reference_build), 'primary_assembly.fa'),
                self.output().path]

    def output(self):
        return luigi.LocalTarget(join(cfg.ASSEMBLIES, 'runtime/{}_{}/{}_0'.format(self.genome_build, self.reference_build, self.taxon)))

class AlignSample(ScheduledExternalProgramTask):
    """
    The output of the task is a pair of isoform and gene quantification results
    processed by STAR and RSEM.

    :ignore_mate:
    """
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    source = luigi.ChoiceParameter(default='local', choices=SAMPLE_SOURCES, positional=False)

    taxon = luigi.Parameter(default='human', positional=False)
    genome_build = luigi.Parameter(default='hg38', positional=False)
    reference_build = luigi.Parameter(default='ncbi', positional=False)

    ignore_mate = luigi.BoolParameter(default=False, positional=False)

    # TODO: handle strand-specific reads
    strand_specific = luigi.BoolParameter(default=False, positional=False)

    scheduler_extra_args = ['--partition', 'Cargo']
    walltime = datetime.timedelta(hours=12)
    cpus = 8
    memory = 32

    def requires(self):
        # FIXME: requiring the second task introduces a bottleneck in the pipeline
        return [DownloadSample(self.experiment_id, self.sample_id, source=self.source), QualityControlSample(self.experiment_id, self.sample_id, source=self.source)]

    def run(self):
        self.output().makedirs()
        return super(AlignSample, self).run()

    def program_args(self):
        args = [join(cfg.RSEM_DIR, 'rsem-calculate-expression'), '-p', self.cpus]

        args.extend([
            '--time',
            '--star',
            '--star-path', cfg.STAR_PATH,
            '--star-gzipped-read-file',
            '--no-bam-output'])

        if self.strand_specific:
            args.append('--strand-specific')

        sample_run, _ = self.input()

        fastqs = [mate.path for mate in sample_run]

        if len(fastqs) == 1:
            args.append(fastqs[0])
        elif len(fastqs) == 2 and self.ignore_mate:
            logger.info('Mate is ignored for {}.'.format(self))
            args.append(fastqs[0])
        elif len(fastqs) == 2:
            args.append('--paired-end')
            args.extend(fastqs)
        else:
            raise ValueError('More than two input FASTQs are not supported.')

        # reference for alignments and quantifications
        args.append(join(cfg.ASSEMBLIES, 'runtime/{}_{}/{}_0'.format(self.genome_build, self.reference_build, self.taxon)))

        # output prefix
        args.append(join(os.path.dirname(self.output().path), self.sample_id))

        return args

    def output(self):
        destdir = join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, '{}_{}'.format(self.genome_build, self.reference_build), self.experiment_id)
        return luigi.LocalTarget(join(destdir, '{}.genes.results'.format(self.sample_id)))

class AlignExperiment(luigi.Task):
    """
    Align all the samples in a given experiment.

    The output is one sample alignment output per sample contained in the
    experiment.
    """
    experiment_id = luigi.Parameter()

    source = luigi.ChoiceParameter(default='local', choices=EXPERIMENT_SOURCES, positional=False)

    taxon = luigi.Parameter(default='human', positional=False)
    genome_build = luigi.Parameter(default='hg38', positional=False)
    reference_build = luigi.Parameter(default='ncbi', positional=False)

    def requires(self):
        return DownloadExperiment(self.experiment_id, source=self.source)

    def run(self):
        samples = self.input()
        yield [AlignSample(self.experiment_id, os.path.basename(os.path.dirname(sample[0].path)),
                           taxon=self.taxon, genome_build=self.genome_build, reference_build=self.reference_build)
               for sample in samples if len(sample) > 0]

    def output(self):
        return [task.output() for task in next(self.run())]

class GenerateReportForExperiment(ExternalProgramTask):
    """
    MultiQC!
    """
    experiment_id = luigi.Parameter()

    source = luigi.ChoiceParameter(default='local', choices=EXPERIMENT_SOURCES, positional=False)

    taxon = luigi.Parameter(default='human')
    genome_build = luigi.Parameter(default='hg38')
    reference_build = luigi.Parameter(default='ncbi')

    def requires(self):
        return AlignExperiment(self.experiment_id, taxon=self.taxon, genome_build=self.genome_build, reference_build=self.reference_build)

    def program_args(self):
        args = ['multiqc',
                '--outdir', os.path.dirname(self.output().path),
                join(cfg.OUTPUT_DIR, cfg.DATAQCDIR, self.experiment_id),
                join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, '{}_{}'.format(self.genome_build, self.reference_build), self.experiment_id)]

        return args

    def run(self):
        self.output().makedirs()
        return super(GenerateReportForExperiment, self).run()

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, 'report2', self.experiment_id, 'multiqc_report.html'))

class CountExperiment(luigi.Task):
    """
    Combine the RSEM quantifications results from all the samples in a given
    experiment.

    The output is two matrices: counts and FPKM.
    """
    experiment_id = luigi.Parameter()

    source = luigi.ChoiceParameter(default='local', choices=EXPERIMENT_SOURCES, positional=False)

    taxon = luigi.Parameter(default='human')
    genome_build = luigi.Parameter(default='hg38')
    reference_build = luigi.Parameter(default='ncbi')

    resources = {'cpus': 1}

    def requires(self):
        return AlignExperiment(self.experiment_id, taxon=self.taxon, genome_build=self.genome_build, reference_build=self.reference_build, source=self.source)

    def run(self):
        # FIXME: this is a hack
        keys = [align_task.sample_id for align_task in next(self.requires().run())]
        counts_df = pd.concat([pd.read_csv(gene.path, sep='\t', index_col=0).expected_count for gene in self.input()], keys=keys, axis=1)
        fpkm_df = pd.concat([pd.read_csv(gene.path, sep='\t', index_col=0).FPKM for gene in self.input()], keys=keys, axis=1)

        with self.output()[0].open('w') as f:
            counts_df.to_csv(f, sep='\t')

        with self.output()[1].open('w') as f:
            fpkm_df.to_csv(f, sep='\t')

    def output(self):
        destdir = join(cfg.OUTPUT_DIR, cfg.QUANTDIR, '{}_{}'.format(self.genome_build, self.reference_build))
        return [luigi.LocalTarget(join(destdir, '{}_counts.genes'.format(self.experiment_id))),
                luigi.LocalTarget(join(destdir, '{}_fpkm.genes'.format(self.experiment_id)))]

class SubmitExperimentToGemma(ExternalProgramTask):
    """
    Submit an experiment to Gemma.

    The metadata containing the taxon are fetched from Gemma REST API.

    This will trigger the whole pipeline.

    The output is a confirmation that the data is effectively in Gemma.
    """
    experiment_id = luigi.Parameter()

    resources = {'gemma_connections': 1}

    @staticmethod
    def get_taxon_for_dataset_short_name(dataset_short_name):
        basic_auth = HTTPBasicAuth(os.getenv('GEMMAUSERNAME'), os.getenv('GEMMAPASSWORD'))
        res = requests.get('https://gemma.msl.ubc.ca/rest/v2/datasets/{}/platforms'.format(dataset_short_name), auth=basic_auth)
        res.raise_for_status()
        return res.json()['data'][0]['taxon']

    @staticmethod
    def get_genome_build_for_taxon(taxon):
        try:
            return {'human': 'hg38', 'mouse': 'mm10', 'rat': 'm6'}[taxon]
        except KeyError:
            raise ValueError('Unsupported Gemma taxon {}.'.format(taxon))

    @staticmethod
    def get_platform_short_name_for_taxon(taxon):
        return 'Generic_{}_ncbiIds'.format(taxon)

    def requires(self):
        taxon = self.get_taxon_for_dataset_short_name(self.experiment_id)
        return CountExperiment(self.experiment_id,
                               taxon=taxon,
                               genome_build=self.get_genome_build_for_taxon(taxon),
                               reference_build='ncbi',
                               source='gemma')

    def program_environment(self):
        return cfg.asenv(['GEMMA_LIB', 'JAVA_HOME', 'JAVA_OPTS'])

    def program_args(self):
        count, fpkm = self.input()
        taxon = self.get_taxon_for_dataset_short_name(self.experiment_id)
        return [cfg.GEMMACLI, 'rnaseqDataAdd',
                '-u', os.getenv('GEMMAUSERNAME'),
                '-p', os.getenv('GEMMAPASSWORD'),
                '-e', self.experiment_id,
                '-a', self.get_platform_short_name_for_taxon(taxon),
                '-count', count.path,
                '-rpkm', fpkm.path]

    def output(self):
        taxon = self.get_taxon_for_dataset_short_name(self.experiment_id)
        return GemmaDatasetHasPlatform(self.experiment_id, self.get_platform_short_name_for_taxon(taxon))

class SubmitExperimentsFromFileToGemma(WrapperTask):
    input_file = luigi.Parameter()
    def requires(self):
        with open(self.input_file) as f:
            return [SubmitExperimentToGemma(line.rstrip()) for line in f]
