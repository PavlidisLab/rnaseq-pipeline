import datetime
from glob import glob
import gzip
import os
from os.path import join
import logging

import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import luigi
import luigi.task
from luigi.task import flatten
from luigi.contrib.external_program import ExternalProgramTask
from luigi.util import requires
from bioluigi.tasks import fastqc, multiqc
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask
import yaml

from .config import rnaseq_pipeline
from .utils import WrapperTask, DynamicWrapperTask
from .sources.geo import DownloadGeoSample, DownloadGeoSeries, ExtractGeoSeriesBatchInfo
from .sources.local import DownloadLocalSample, DownloadLocalExperiment
from .sources.gemma import DownloadGemmaExperiment
from .sources.arrayexpress import DownloadArrayExpressSample, DownloadArrayExpressExperiment
from .targets import GemmaDatasetHasPlatform

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

    source = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'arrayexpress', 'local'], positional=False)

    def requires(self):
        if self.source in ['geo', 'gemma']:
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

    source = luigi.ChoiceParameter(default='local', choices=['gemma', 'geo', 'arrayexpress', 'local'], positional=False)

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
        samples = self.input()
        # FIXME: have a more reliable way to determine the sample id
        yield [QualityControlSample(self.experiment_id,
                                    os.path.basename(os.path.dirname(sample[0].path)),
                                    source=self.source)
               for sample in samples if len(sample) > 0]

class PrepareReference(ScheduledExternalProgramTask):
    """
    Prepare a STAR/RSEM reference.

    :param taxon: Taxon
    :param genome_build: Genome build to use (i.e. hg19, hg38)
    :param reference_build: Reference annotation build to use (i.e. ensembl98, ncbi)
    """
    taxon = luigi.Parameter(default='human')
    genome_build = luigi.Parameter(default='hg38')
    reference_build = luigi.Parameter(default='ncbi')

    walltime = datetime.timedelta(hours=12)
    cpus = 16
    memory = 32

    def input(self):
        assembly_dir=join(cfg.ASSEMBLIES, '{}_{}'.format(self.genome_build, self.reference_build))
        return [[luigi.LocalTarget(f) for f in glob(join(assembly_dir, '*.gtf'))],
                [luigi.LocalTarget(f) for f in glob(join(assembly_dir, '*.fa'))]]

    def program_args(self):
        gtf, genome_fasta = self.input()
        args = [join(cfg.RSEM_DIR, 'rsem-prepare-reference')]

        args.extend([t.path for t in gtf])

        args.extend([
            '--star',
            '-p', self.cpus])

        args.extend([t.path for t in genome_fasta])

        args.append(self.output().path)

        return args

    def output(self):
        return luigi.LocalTarget(join(cfg.ASSEMBLIES, 'runtime/{}_{}'.format(self.genome_build, self.reference_build, self.taxon)))

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

    walltime = datetime.timedelta(hours=12)
    cpus = 8
    memory = 32

    retry_count = 0

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

        sample_run, qc_run, reference = self.input()

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
            raise ValueError('More than two input FASTQs are not supported.')

        # reference for alignments and quantifications
        args.append(join(reference.path, '{}_0'.format(self.taxon)))

        # output prefix
        args.append(join(os.path.dirname(self.output().path), self.sample_id))

        return args

    def output(self):
        destdir = join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, '{}_{}'.format(self.genome_build, self.reference_build), self.experiment_id)
        return luigi.LocalTarget(join(destdir, '{}.genes.results'.format(self.sample_id)))

@requires(DownloadExperiment)
class AlignExperiment(DynamicWrapperTask):
    """
    Align all the samples in a given experiment.

    The output is one sample alignment output per sample contained in the
    experiment.
    """
    taxon = luigi.Parameter(default='human', positional=False)
    genome_build = luigi.Parameter(default='hg38', positional=False)
    reference_build = luigi.Parameter(default='ncbi', positional=False)

    def run(self):
        samples = self.input()
        # FIXME: have a more reliable way to determine the sample id
        yield [AlignSample(self.experiment_id,
                           os.path.basename(os.path.dirname(sample[0].path)),
                           source=self.source,
                           taxon=self.taxon,
                           genome_build=self.genome_build,
                           reference_build=self.reference_build)
               for sample in samples if len(sample) > 0]

@requires(QualityControlExperiment,AlignExperiment)
class GenerateReportForExperiment(luigi.Task):
    """
    Generate a summary report for an experiment with MultiQC.

    The report include collected FastQC reports and RSEM/STAR outputs.
    """

    def run(self):
        search_dirs = set()
        search_dirs.update(os.path.dirname(out.path) for out in flatten(self.input()))
        self.output().makedirs()
        yield multiqc.GenerateReport(list(search_dirs),
                                     os.path.dirname(self.output().path))

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, 'report', '{}_{}'.format(self.genome_build, self.reference_build), self.experiment_id, 'multiqc_report.html'))

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
    def get_dataset_info(dataset_short_name):
        basic_auth = HTTPBasicAuth(os.getenv('GEMMAUSERNAME'), os.getenv('GEMMAPASSWORD'))
        res = requests.get('https://gemma.msl.ubc.ca/rest/v2/datasets/{}'.format(dataset_short_name), auth=basic_auth)
        res.raise_for_status()
        return res.json()['data'][0]

    @staticmethod
    def get_taxon_for_dataset_short_name(dataset_short_name):
        basic_auth = HTTPBasicAuth(os.getenv('GEMMAUSERNAME'), os.getenv('GEMMAPASSWORD'))
        res = requests.get('https://gemma.msl.ubc.ca/rest/v2/datasets/{}'.format(dataset_short_name), auth=basic_auth)
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
        dataset_info = self.get_dataset_info(self.experiment_id)

        taxon = dataset_info['taxon']

        yield CountExperiment(self.experiment_id,
                              taxon=taxon,
                              genome_build=self.get_genome_build_for_taxon(taxon),
                              reference_build='ncbi',
                              source='gemma')

        # If the experiment id refers to a GEO Series, we also want to extract
        # its batch information
        #
        # If the GEO Series was split into multiple Gemma datasets, this will
        # be marked by a '.'
        #
        # TOOD: Have a generic strategy for extracting batch info
        # FIXME: this can result in unexpected sample from GEO being included
        if dataset_info['externalDatabase'] == 'GEO':
            yield ExtractGeoSeriesBatchInfo(dataset_info['accession'])
        else:
            yield None

        # FIXME: this does not always trigger the dependencies
        yield GenerateReportForExperiment(self.experiment_id,
                                          taxon=taxon,
                                          genome_build=self.get_genome_build_for_taxon(taxon),
                                          reference_build='ncbi',
                                          source='gemma')

    def program_environment(self):
        return cfg.asenv(['GEMMA_LIB', 'JAVA_HOME', 'JAVA_OPTS'])

    def program_args(self):
        (count, fpkm), batch_info, multiqc_report = self.input()
        taxon = self.get_taxon_for_dataset_short_name(self.experiment_id)
        # TODO: submit the batch information and the MultiQC report
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
