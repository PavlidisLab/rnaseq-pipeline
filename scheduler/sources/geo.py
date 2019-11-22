import datetime
import logging
import shlex
from subprocess import Popen, check_call, PIPE
import os
from os.path import join
import urllib
import tarfile

import luigi
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask
from bioluigi.tasks import sratoolkit
import pandas as pd

from ..config import rnaseq_pipeline
from ..utils import WrapperTask, NonAtomicTaskRunContext
from ..miniml_utils import extract_rnaseq_gsm

cfg = rnaseq_pipeline()

logger = logging.getLogger('luigi-interface')

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

    scheduler_extra_args = ['--partition', 'Cargo']
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
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}.csv'.format(self.gsm)))

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
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}_family.xml'.format(self.gse)))

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
