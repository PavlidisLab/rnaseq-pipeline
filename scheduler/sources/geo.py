import datetime
import gzip
import logging
import shlex
from subprocess import Popen, check_call, PIPE
import os
from os.path import join
import urllib
import tarfile

import luigi
from luigi.util import requires
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask
from bioluigi.tasks import sratoolkit
import pandas as pd

from ..config import rnaseq_pipeline
from ..utils import WrapperTask, NonAtomicTaskRunContext
from ..miniml_utils import find_rnaseq_geo_samples, collect_geo_samples_info

"""
This module contains all the logic to retrieve RNA-Seq data from GEO and SRA
databases.
"""

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
                                  extra_args=shlex.split(cfg.PREFETCH_ARGS),
                                  scheduler_extra_args=['--partition', 'Wormhole'])

    def output(self):
        return luigi.LocalTarget(join(cfg.SRA_PUBLIC_DIR, '{}.sra'.format(self.srr)))

@requires(PrefetchSraFastq)
class ExtractSraFastq(ScheduledExternalProgramTask):
    """
    Extract FASTQs from a SRR archive

    FASTQs are organized by :gsm: in a flattened layout.

    :param gsm: Geo Sample identifier
    """
    gsm = luigi.Parameter()

    paired_reads = luigi.BoolParameter(positional=False)

    scheduler_extra_args = ['--partition', 'Cargo']
    walltime = datetime.timedelta(hours=6)
    cpus = 1
    memory = 1

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

@requires(DownloadGeoSampleMetadata)
class DownloadGeoSample(luigi.Task):
    """
    Download all SRR related to a GSM
    """

    def run(self):
        # this will raise an error of no FASTQs are related
        df = pd.read_csv(self.input().path)

        # Some GSM happen to have many related SRA runs and we cannot
        # realistically investigate why that is. Our best bet at this point is
        # that the latest properly represents the sample
        latest_run = df.sort_values('Run', ascending=False).iloc[0]

        yield ExtractSraFastq(latest_run.Run, self.gsm, paired_reads=latest_run.LibraryLayout == 'PAIRED')

    def output(self):
        if self.requires().complete():
            try:
                return next(self.run()).output()
            except pd.errors.EmptyDataError:
                logger.exception('%s has no related SRA RNA-Seq runs.', self.gsm)
        return super(DownloadGeoSample, self).output()

class DownloadGeoSeriesMetadata(luigi.Task):
    gse = luigi.Parameter()

    resources = {'geo_ftp_connections': 1}

    def run(self):
        destdir = os.path.dirname(self.output().path)
        metadata_xml_tgz = join(destdir, '{}_family.xml.tgz'.format(self.gse))

        # download compressed metadata
        # FIXME: use Entrez Web API
        urllib.urlretrieve('ftp://ftp.ncbi.nlm.nih.gov/geo/series/{0}/{1}/miniml/{1}_family.xml.tgz'.format(self.gse[:-3] + 'nnn', self.gse),
                           reporthook=lambda numblocks, blocksize, totalsize: self.set_progress_percentage(100.0 * numblocks * blocksize / totalsize),
                           filename=metadata_xml_tgz)

        # extract metadata
        # FIXME: this is not atomic
        with tarfile.open(metadata_xml_tgz, 'r:gz') as tf:
            tf.extract(os.path.basename(self.output().path), destdir)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}_family.xml'.format(self.gse)))

@requires(DownloadGeoSeriesMetadata)
class DownloadGeoSeries(luigi.Task):
    """
    Download all GSM related to a GSE
    """

    def run(self):
        gsms = find_rnaseq_geo_samples(self.input().path)
        if not gsms:
            raise ValueError('{} has no related GEO samples with RNA-Seq data.'.format(self.gse))
        yield [DownloadGeoSample(gsm) for gsm in gsms]

    def output(self):
        if self.requires().complete():
            # FIXME: this is ugly
            try:
                return [task.output() for task in next(self.run())]
            except ValueError:
                logger.exception('%s has no related GEO samples with RNA-Seq data.', self.gse)
        return super(DownloadGeoSeries, self).output()

@requires(DownloadGeoSeriesMetadata, DownloadGeoSeries)
class ExtractGeoSeriesBatchInfo(luigi.Task):
    """
    Extract the GEO Series batch information by looking up the GEO Series
    metadata and some downloaded FASTQs headers.
    """

    def run(self):
        geo_series_metadata, samples = self.input()
        sample_geo_metadata = collect_geo_samples_info(geo_series_metadata.path)
        with self.output().open('w') as info_out:
            for sample in samples:
                fastq = sample[0]
                sample_id = os.path.basename(os.path.dirname(fastq.path))
                fastq_name, _ = os.path.splitext(fastq.path)
                fastq_name, _ = os.path.splitext(fastq_name)
                fastq_id = os.path.basename(fastq_name).split('_')[0]
                gse_id, platform_id, srx_uri = sample_geo_metadata[sample_id]
                with gzip.open(fastq.path, 'rt') as f:
                    fastq_header = f.readline().rstrip()
                info_out.write('\t'.join([sample_id, fastq_id, platform_id, srx_uri, fastq_header]) + '\n')

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, 'fastq_headers', '{}.fastq-headers-table.txt'.format(self.gse)))
