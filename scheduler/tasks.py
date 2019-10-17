import luigi
import luigi.task
from luigi.contrib.external_program import ExternalProgramTask
import os
from subprocess import call, check_output
from shutil import copyfile
from base64 import b64encode
import uuid
from os.path import join
from gemmaclient import GemmaClientAPI
import pandas as pd
import urllib
from subprocess import check_call
import gzip
import tarfile
from miniml_utils import extract_rnaseq_gsm
import shlex

# see luigi.cfg for details
class rnaseq_pipeline(luigi.Config):
    SCRIPTS = luigi.Parameter()
    ROOT_DIR = luigi.Parameter()
    RESULTS_DIR = luigi.Parameter()
    SCRATCH_DIR = luigi.Parameter()
    ASSEMBLIES = luigi.Parameter()
    REQUIREMENTS = luigi.Parameter()
    SCRIPTS = luigi.Parameter()
    DATA = luigi.Parameter()
    QUANTDIR = luigi.Parameter()
    TMPDIR = luigi.Parameter()
    COUNTDIR = luigi.Parameter()

    PREFETCH_EXE = luigi.Parameter()
    PREFETCH_ARGS = luigi.Parameter()
    SRA_PUBLIC_DIR = luigi.Parameter()

    FASTQDUMP_EXE = luigi.Parameter()

    STAR_PATH = luigi.Parameter()
    STAR_MAX_BAM_RAM = luigi.Parameter()
    STAR_SAM_MAPPING = luigi.Parameter()
    STAR_SHARED_MEMORY = luigi.Parameter()

    RSEM_DIR = luigi.Parameter()

    GEMMACLI = luigi.Parameter()
    GEMMA_LIB = luigi.Parameter()
    JAVA_HOME = luigi.Parameter()
    JAVA_OPTS = luigi.Parameter()

    def asenv(self, attrs):
        return {attr: getattr(self, attr) for attr in attrs}

class MetaTaskMixin(object):
    """
    Mixin that ensures that the task output is its requirements outputs.
    """
    def output(self):
        return [elem.output() for elem in luigi.task.flatten(self.requires())]

class PrefetchSRR(ExternalProgramTask):
    """
    Prefetch a SRR sample using prefetch
    """
    srr = luigi.Parameter()

    # FIXME: prefetch sometimes fail and will leave heavy temporary files
    # behind
    retry_count = 5

    resources = {'cpu': 1}

    def program_args(self):
        return [rnaseq_pipeline().PREFETCH_EXE] + shlex.split(rnaseq_pipeline().PREFETCH_ARGS) #, '--ascp-path', rnaseq_pipeline().PREFETCH_ASCP_PATH, self.srr]

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().SRA_PUBLIC_DIR, '{}.sra'.format(self.srr)))

class ExtractSRR(ExternalProgramTask):
    """
    Download FASTQ
    """
    gse = luigi.Parameter()
    gsm = luigi.Parameter()
    srr = luigi.Parameter()

    paired_reads = luigi.BoolParameter()

    resources = {'cpu': 1}

    def requires(self):
        return PrefetchSRR(self.srr)

    def program_args(self):
        return [rnaseq_pipeline().PREFETCH_EXE, self.srr]

    def program_args(self):
        # FIXME: this is not atomic
        return [rnaseq_pipeline().FASTQDUMP_EXE,
                '--gzip', '--clip',
                '--skip-technical',
                '--readids',
                '--dumpbase',
                '--split-files',
                '--outdir', os.path.dirname(self.output().path),
                self.input().path]

    def output(self):
        if self.paired_reads:
            return [luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.gse, self.gsm, self.srr + '_1.fastq.gz')),
                    luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.gse, self.gsm, self.srr + '_2.fastq.gz'))]
        else:
            return [luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.gse, self.gsm, self.srr + '_1.fastq.gz'))]

class DownloadGSMMetadata(luigi.Task):
    gse = luigi.Parameter()
    gsm = luigi.Parameter()

    def run(self):
        # TODO: find a nicer way to query this data
        with self.output().temporary_path() as dest_filename:
            urllib.urlretrieve('https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&amp;db=sra&amp;rettype=runinfo&amp;term={}'.format(self.gsm),
                               filename=dest_filename)

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.gse, 'METADATA', '{}.csv'.format(self.gsm)))

class DownloadGSM(ExternalProgramTask):
    """
    Download all SRR related to a GSM
    """
    gse = luigi.Parameter()
    gsm = luigi.Parameter()

    def requires(self):
        return DownloadGSMMetadata(self.gse, self.gsm)

    def run(self):
        # find all SRA runs associated to this GSM
        df = pd.read_csv(self.input().path)
        yield [ExtractSRR(self.gse, self.gsm, run.Run, run.LibraryLayout == 'PAIRED')
                for _, run in df.iterrows()]

    def output(self):
        # this needs to be satisfied first
        if self.input().exists():
            return [task.output() for task in next(self.run())]
        else:
            return []

class DownloadGSEMetadata(luigi.Task):
    gse = luigi.Parameter()

    def run(self):
        # ensure that the download path exists
        self.output().makedirs()

        # download compressed metadata
        # FIXME: this is not atomic
        metadata_xml_tgz = join(os.path.dirname(self.output().path), '{}_family.xml.tgz'.format(self.gse))
        urllib.urlretrieve('ftp://ftp.ncbi.nlm.nih.gov/geo/series/{0}/{1}/miniml/{1}_family.xml.tgz'.format(self.gse[:-3] + 'nnn', self.gse),
                           filename=metadata_xml_tgz)

        # extract metadata
        # FIXME: this is not atomic
        with tarfile.open(metadata_xml_tgz, 'r:gz') as tf:
            tf.extract('{}_family.xml'.format(self.gse), os.path.dirname(self.output().path))

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.gse, 'METADATA', '{}_family.xml'.format(self.gse)))

class DownloadGSE(luigi.Task):
    """
    Download all GSM related to a GSE
    """
    gse = luigi.Parameter()

    def requires(self):
        return DownloadGSEMetadata(self.gse)

    def run(self):
        # parse MINiML format to get GSM and download each of them
        yield [DownloadGSM(self.gse, gsm)
                for gsm in extract_rnaseq_gsm(self.input().path)]

    def output(self):
        # this needs to be satisfied first
        if self.input().exists():
            return [DownloadGSM(self.gse, gsm).output()
                        for gsm in extract_rnaseq_gsm(self.input().path)]
        else:
            return []

class DownloadArrayExpressSample(luigi.Task):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()
    # TODO: remove this URL
    sample_url = luigi.Parameter()

    def run(self):
        with self.output().temporary_path() as dest_filename:
            urllib.urlretrieve(self.sample_url, filename=dest_filename)

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.experiment_id, self.sample_id, os.path.basename(self.sample_url)))

class DownloadArrayExpressExperiment(luigi.Task):
    """
    Download all the related ArrayExpress sample to this ArrayExpress experiment.
    """
    experiment_id = luigi.Parameter()
    def run(self):
        ae_df = pd.read_csv('http://www.ebi.ac.uk/arrayexpress/files/{0}/{0}.sdrf.txt'.format(self.experiment_id), sep='\t')
        yield [DownloadArrayExpressSample(experiment_id=self.experiment_id, sample_id=s['Comment[ENA_RUN]'], sample_url=s['Comment[FASTQ_URI]'])
                for ix, s in ae_df.iterrows()]

    def output():
        # FIXME: we should not run this here...
        return [task.output() for task in next(self.run())]

class DownloadSample(luigi.Task, MetaTaskMixin):
    """
    This is a generic task for downloading an individual sample in an
    experiment.
    """
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    def requires(self):
        if self.experiment_id.startswith('GSE'):
            return DownloadGSM(self.experiment_id, self.sample_id)
        else:
            return DownloadArrayExpressSample(self.experiment_id, self.sample_id)

class DownloadExperiment(luigi.Task, MetaTaskMixin):
    """
    This is a generic task that detects which kind of experiment is intended to
    be downloaded so that downstream tasks can process regardless of the data
    source.
    """
    experiment_id = luigi.Parameter()
    def requires(self):
        if self.experiment_id.startswith('GSE'):
            return DownloadGSE(self.experiment_id)
        else:
            return DownloadArrayExpressExperiment(self.experiment_id)

class AlignSample(ExternalProgramTask):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    reference = luigi.Parameter(default='human')
    reference_build = luigi.Parameter(default='ncbi38')

    # this setup should allow us to run 16 parallel jobs
    resources = {'cpu': 4, 'mem': 32}

    def requires(self):
        # FIXME: put this in run
        self.output()[0].makedirs()
        check_output(['mkdir', '-p', join(rnaseq_pipeline().TMPDIR, self.experiment_id, self.sample_id)])
        return DownloadSample(self.experiment_id, self.sample_id)

    def program_args(self):
        args = [join(rnaseq_pipeline().RSEM_DIR, 'rsem-calculate-expression'), '-p', self.resources['cpu']]

        args.extend([
            '--time',
            '--star',
            '--star-path', rnaseq_pipeline().STAR_PATH,
            '--star-gzipped-read-file',
            '--temporary-folder', join(rnaseq_pipeline().TMPDIR, self.experiment_id, self.sample_id)])

        if len(self.input()) != 1:
            raise ValueError('The alignment step requires exactly one RNA-Seq dataset per sample.')

        fastqs = [mate.path for mate in self.input()[0]]

        if len(fastqs) == 1:
            pass # single-ended (default)
        elif len(fastqs) == 2:
            args.append('--paired-end')
        else:
            raise ValueError('More than two input FASTQs are not supported.')

        args.extend(fastqs)

        # STAR reference
        args.append('/space/grp/Pipelines/rnaseq-pipeline/Assemblies/runtime/{0}_ref{1}/{0}_0'.format(self.reference, self.reference_build))

        # output
        args.append(join(rnaseq_pipeline().QUANTDIR, self.experiment_id, self.sample_id))

        args.extend([
            '--star-shared-memory', rnaseq_pipeline().STAR_SHARED_MEMORY,
            '--keep-intermediate-files'])

        return args

    def output(self):
        destdir = join(rnaseq_pipeline().QUANTDIR, self.experiment_id)
        return [luigi.LocalTarget(join(destdir, '{}.isoforms.results'.format(self.sample_id))),
                luigi.LocalTarget(join(destdir, '{}.genes.results'.format(self.sample_id)))]

class AlignExperiment(luigi.Task):
    experiment_id = luigi.Parameter()

    reference = luigi.Parameter(default='human')
    reference_build = luigi.Parameter(default='ncbi38')

    def requires(self):
        return DownloadExperiment(self.experiment_id)

    def run(self):
        # FIXME: do this better
        yield [AlignSample(self.experiment_id, os.path.basename(os.path.dirname(sample[0][0].path)), self.reference, self.reference_build)
                for sample in self.input()]

    def output(self):
        return [AlignSample(self.experiment_id, os.path.basename(os.path.dirname(sample[0][0].path)), self.reference, self.reference_build).output()
                    for sample in self.input()]

class CountExperiment(ExternalProgramTask):
    experiment_id = luigi.Parameter()

    reference = luigi.Parameter(default='human')
    reference_build = luigi.Parameter(default='ncbi38')

    scope = luigi.Parameter(default='genes')

    resources = {'cpu': 1}

    def requires(self):
        return AlignExperiment(self.experiment_id, self.reference, self.reference_build)

    def program_args(self):
        return [join(rnaseq_pipeline().ROOT_DIR, 'Pipelines/rsem/rsem_count.sh'), join(rnaseq_pipeline().QUANTDIR, self.experiment_id), self.scope]

    def program_environment(self):
        return rnaseq_pipeline().asenv(['RSEM_DIR'])

    def output(self):
        destdir = join(rnaseq_pipeline().QUANTDIR, self.experiment_id)
        return [luigi.LocalTarget(join(destdir, 'countMatrix.{}'.format(self.scope))),
                luigi.LocalTarget(join(destdir, 'tpmMatrix.{}'.format(self.scope))),
                luigi.LocalTarget(join(destdir, 'fpkmMatrix.{}'.format(self.scope)))]

class SubmitExperimentToGemma(ExternalProgramTask):
    """
    Load experiment into Gemma.
    """
    experiment_id = luigi.Parameter()

    reference = luigi.Parameter(default='human')
    reference_build = luigi.Parameter(default='ncbi38')

    def requires(self):
        return CountExperiment(self.experiment_id, self.reference, self.reference_build)

    def program_environment(self):
        return rnaseq_pipeline().asenv(['GEMMA_LIB', 'JAVA_HOME', 'JAVA_OPTS'])

    def program_args(self):
        count, tpm, fpkm = self.input()
        return [rnaseq_pipeline().GEMMACLI, 'rnaseqDataAdd',
                '-u', os.getenv('GEMMAUSERNAME'),
                '-p', os.getenv('GEMMAPASSWORD'),
                '-e', self.experiment_id,
                '-a', 'Generic_{}_ensemblIds'.format(self.reference),
                '-count', count.path,
                '-rpkm', fpkm.path]

    def output(self):
        # check if data is in Gemma
        pass
