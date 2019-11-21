import datetime
import os
from os.path import join
from subprocess import Popen, check_call, PIPE
import urllib
import tarfile
import shlex
from glob import glob
import tempfile
import logging

import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import luigi
import luigi.task
from luigi.contrib.external_program import ExternalProgramTask
from bioluigi.tasks import sratoolkit, fastqc
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask

from .config import rnaseq_pipeline
from .utils import WrapperTask, NonAtomicTaskRunContext
from .miniml_utils import extract_rnaseq_gsm
from .targets import GemmaDatasetHasPlatform

EXPERIMENT_SOURCES = ['gemma', 'geo', 'arrayexpress', 'local']
SAMPLE_SOURCES = ['geo', 'arrayexpress', 'local']

logger = logging.getLogger('luigi-interface')

cfg = rnaseq_pipeline()

class PrefetchSraFastq(luigi.Task):
    """
    Prefetch a SRR sample using prefetch

    Data is downloaded in a shared SRA cache.
    """
    srr = luigi.Parameter()

    resources = {'sra_connections': 1}

    def run(self):
        yield sratoolkit.Prefetch(self.srr,
                                  self.output().path,
                                  max_size=30,
                                  extra_args=shlex.split(cfg.PREFETCH_ARGS))

    def output(self):
        return luigi.LocalTarget(join(cfg.SRA_PUBLIC_DIR, '{}.sra'.format(self.srr)))

class ExtractSraFastq(ScheduledExternalProgramTask):
    """
    Extract FASTQs from a SRR archive

    FASTQs are organized by :gsm: in a flattened layout.
    """
    gsm = luigi.Parameter()
    srr = luigi.Parameter()

    paired_reads = luigi.BoolParameter(positional=False)

    scheduler_extra_args = ['--partition', 'All']
    walltime = datetime.timedelta(hours=6)
    cpus = 1
    memory = 1

    def requires(self):
        return PrefetchSraFastq(self.srr)

    def program_args(self):
        # FIXME: this is not atomic
        # FIXME: use fasterq-dump
        return [cfg.FASTQDUMP_EXE,
                '--gzip',
                '--clip',
                '--skip-technical',
                '--readids',
                '--dumpbase',
                '--split-files',
                '--disable-multithreading', # TODO: this is a fairly recent flag, so it would be nice to do a version-check
                '--outdir', os.path.dirname(self.output()[0].path),
                self.input().path]

    def run(self):
        with NonAtomicTaskRunContext(self):
            return super(ExtractSraFastq, self).run()

    def output(self):
        if self.paired_reads:
            return [luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.DATA, 'geo', self.gsm, self.srr + '_1.fastq.gz')),
                    luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.DATA, 'geo', self.gsm, self.srr + '_2.fastq.gz'))]
        else:
            return [luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.DATA, 'geo', self.gsm, self.srr + '_1.fastq.gz'))]

class DownloadGeoSampleMetadata(luigi.Task):
    gsm = luigi.Parameter()

    resources = {'edirect_http_connections': 1}

    def run(self):
        with self.output().open('w') as f:
            esearch_proc = Popen(['Requirements/edirect/esearch', '-db', 'sra', '-query', self.gsm], stdout=PIPE)
            check_call(['Requirements/edirect/efetch', '-format', 'runinfo'], stdin=esearch_proc.stdout, stdout=f)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, '{}.csv'.format(self.gsm)))

class DownloadGeoSample(luigi.Task):
    """
    Download all SRR related to a GSM
    """
    gsm = luigi.Parameter()

    def requires(self):
        return DownloadGeoSampleMetadata(self.gsm)

    def run(self):
        # this will raise an error of no FASTQs are related
        df = pd.read_csv(self.input().path)

        # Some GSM happen to have many related samples and we cannot
        # realistically investigate why that is. Our best bet at this point
        # is that the latest SRR properly represents the sample
        latest_run = df.sort_values('Run', ascending=False).iloc[0]

        yield ExtractSraFastq(self.gsm, latest_run.Run, paired_reads=latest_run.LibraryLayout == 'PAIRED')

    def output(self):
        if self.requires().complete():
            try:
                return next(self.run()).output()
            except pd.errors.EmptyDataError:
                logger.exception('{} has no related SRA RNA-Seq runs.'.format(self.gsm))
        return super(DownloadGeoSample, self).output()

class DownloadGeoSeriesMetadata(luigi.Task):
    gse = luigi.Parameter()

    resources = {'geo_ftp_connections': 1}

    def run(self):
        destdir = os.path.dirname(self.output().path)
        metadata_xml_tgz = join(destdir, '{}_family.xml.tgz'.format(self.gse))
        metadata_xml = join(destdir, '{}_family.xml'.format(self.gse))

        # download compressed metadata
        # FIXME: use Entrez Web API
        urllib.urlretrieve('ftp://ftp.ncbi.nlm.nih.gov/geo/series/{0}/{1}/miniml/{1}_family.xml.tgz'.format(self.gse[:-3] + 'nnn', self.gse),
                reporthook=lambda numblocks, blocksize, totalsize: self.set_progress_percentage(100.0 * numblocks * blocksize / totalsize),
                filename=metadata_xml_tgz)

        # extract metadata
        # FIXME: this is not atomic
        with tarfile.open(metadata_xml_tgz, 'r:gz') as tf:
            tf.extract('{}_family.xml'.format(self.gse), destdir)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, '{}_family.xml'.format(self.gse)))

class DownloadGeoSeries(luigi.Task):
    """
    Download all GSM related to a GSE
    """
    gse = luigi.Parameter()

    def requires(self):
        return DownloadGeoSeriesMetadata(self.gse)

    def run(self):
        gsms = extract_rnaseq_gsm(self.input().path)
        if not gsms:
            raise ValueError('{} has no related GEO samples with RNA-Seq data.'.format(self.gse))
        yield [DownloadGeoSample(gsm) for gsm in gsms]

    def output(self):
        if self.requires().complete():
            # FIXME: this is ugly
            try:
                return [task.output() for task in next(self.run())]
            except ValueError:
                logger.exception('{} has no related GEO samples with RNA-Seq data.'.format(self.gse))
        return super(DownloadGeoSeries, self).output()

class DownloadArrayExpressFastq(luigi.Task):
    sample_id = luigi.Parameter()
    fastq_url = luigi.Parameter()

    resources = {'array_express_http_connections': 1}

    def run(self):
        with self.output().temporary_path() as dest_filename:
            urllib.urlretrieve(self.fastq_url,
                    reporthook=lambda numblocks, blocksize, totalsize: self.set_progress_percentage(100.0 * numblocks * blocksize / totalsize),
                    filename=dest_filename)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.DATA, 'arrayexpress', self.sample_id, os.path.basename(self.fastq_url)))

class DownloadArrayExpressSample(WrapperTask):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()
    fastq_urls = luigi.ListParameter()

    def requires(self):
        return [DownloadArrayExpressFastq(self.sample_id, fastq_url) for fastq_url in self.fastq_urls]

class DownloadArrayExpressExperiment(WrapperTask):
    """
    Download all the related ArrayExpress sample to this ArrayExpress experiment.
    """
    experiment_id = luigi.Parameter()

    def requires(self):
        ae_df = pd.read_csv('http://www.ebi.ac.uk/arrayexpress/files/{0}/{0}.sdrf.txt'.format(self.experiment_id), sep='\t')
        # FIXME: properly handle the order of paired FASTQs
        return [DownloadArrayExpressSample(experiment_id=self.experiment_id, sample_id=sample_id, fastq_urls=s['Comment[FASTQ_URI]'].sort_values().tolist())
                for sample_id, s in ae_df.groupby('Comment[ENA_SAMPLE]')]

class DownloadLocalSample(luigi.Task):
    """
    Local samples are organized by :experiment_id: to avoid name clashes across
    experiments.
    """
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    def output(self):
        # we sort to make sure that pair ends are in correct order
        return [luigi.LocalTarget(f) for f in sorted(glob(join(cfg.OUTPUT_DIR, cfg.DATA, 'local', self.experiment_id, self.sample_id, '*.fastq.gz')))]

class DownloadLocalExperiment(WrapperTask):
    experiment_id = luigi.Parameter()

    def requires(self):
        return [DownloadLocalSample(self.experiment_id, os.path.basename(f))
                for f in glob(join(cfg.OUTPUT_DIR, cfg.DATA, 'local', self.experiment_id, '*'))]

class DownloadGemmaExperiment(WrapperTask):
    """
    Download an experiment described by a Gemma dataset using the REST API.

    Gemma itself does not retain raw data, so this task delegate the work to
    other sources.
    """
    experiment_id = luigi.Parameter()

    def requires(self):
        res = requests.get('http://gemma.msl.ubc.ca/rest/v2/datasets/{}/samples'.format(self.experiment_id), auth=HTTPBasicAuth(os.getenv('GEMMAUSERNAME'), os.getenv('GEMMAPASSWORD')))
        res.raise_for_status()
        return [DownloadGeoSample(sample['accession']['accession'])
                    for sample in res.json()['data']
                        if sample['accession']['externalDatabase']['name'] == 'GEO']

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
                    scheduler_extra_args=['--partition', 'All'])

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

    scheduler_extra_args = ['--partition', 'All']
    walltime = datetime.timedelta(hours=12)
    cpus = 16
    memory = 32

    def program_args(self):
        return [join(cfg.RSEM_DIR, 'rsem-prepare-reference'),
                join(cfg.ASSEMBLIES, '{}_{}'.format(self.genome_build, self.reference_build, '*.gtf')),
                '--star',
                '--star-path', cfg.STAR_PATH,
                '-p', self.cpus,
                join(cfg.ASSEMBLIES, '{}_{}'.format(self.genome_build, self.reference_build, 'primary_assembly.fa')),
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

    scheduler_extra_args = ['--partition', 'All']
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

        sample_run, qc_run = self.input()

        fastqs = [mate.path for mate in sample_run]

        if len(fastqs) == 1:
            args.append(fastqs[0])
        elif len(fastqs) == 2 and self.ignore_mate:
            logger.info('Mate is ignored for {}.'.format(self))
            args.append(fastqs[0])
        elif len(fastqs) == 2 :
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
