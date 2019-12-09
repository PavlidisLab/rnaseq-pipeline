import gzip
import logging
from subprocess import Popen, check_call, PIPE
import os
from os.path import join
import urllib
import tarfile

import luigi
from luigi.util import requires
import pandas as pd

from ..config import rnaseq_pipeline
from ..miniml_utils import collect_geo_samples_with_rnaseq_data, collect_geo_samples_info
from ..utils import DynamicWrapperTask

"""
This module contains all the logic to retrieve RNA-Seq data from GEO.
"""

cfg = rnaseq_pipeline()

logger = logging.getLogger('luigi-interface')

from .sra import DumpSraFastq

class DownloadGeoSampleRunInfo(luigi.Task):
    """
    Download all related SRA run infos from a GEO Sample.

    TODO: use the related SRA Experiment to do this, because esearch does not
    always work reliably given GEO Sample identifiers.
    """
    gsm = luigi.Parameter()

    resources = {'edirect_http_connections': 1}

    def run(self):
        with self.output().open('w') as f:
            esearch_proc = Popen(['Requirements/edirect/esearch', '-db', 'sra', '-query', self.gsm], stdout=PIPE)
            check_call(['Requirements/edirect/efetch', '-format', 'runinfo'], stdin=esearch_proc.stdout, stdout=f)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}.csv'.format(self.gsm)))

@requires(DownloadGeoSampleRunInfo)
class DownloadGeoSample(DynamicWrapperTask):
    """
    Download a GEO Sample given a runinfo file and
    """

    retry_count = 0

    def run(self):
        # this will raise an error of no FASTQs are related
        df = pd.read_csv(self.input().path)

        # Some GSM happen to have many related SRA runs and we cannot
        # realistically investigate why that is. Our best bet at this point is
        # that the latest properly represents the sample
        latest_run = df.sort_values('Run', ascending=False).iloc[0]

        yield DumpSraFastq(latest_run.Run, self.gsm, paired_reads=latest_run.LibraryLayout == 'PAIRED')

class DownloadGeoSeriesMetadata(luigi.Task):
    """
    Download a GEO Series metadata containg information about related GEO
    Samples.
    """
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
class DownloadGeoSeries(DynamicWrapperTask):
    """
    Download all GEO Samples related to a GEO Series.
    """

    retry_count = 0

    def run(self):
        gsms = collect_geo_samples_with_rnaseq_data(self.input().path)
        if not gsms:
            raise ValueError('{} has no related GEO samples with RNA-Seq data.'.format(self.gse))
        yield [DownloadGeoSample(gsm) for gsm in gsms]

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
                if len(sample) == 0:
                    # FIXME:
                    continue
                fastq = sample[0]
                sample_id = os.path.basename(os.path.dirname(fastq.path))
                fastq_name, _ = os.path.splitext(fastq.path)
                fastq_name, _ = os.path.splitext(fastq_name)
                fastq_id = os.path.basename(fastq_name).split('_')[0]
                platform_id, srx_uri = sample_geo_metadata[sample_id]
                with gzip.open(fastq.path, 'rt') as f:
                    fastq_header = f.readline().rstrip()
                info_out.write('\t'.join([sample_id, fastq_id, platform_id, srx_uri, fastq_header]) + '\n')

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, 'fastq_headers', '{}.fastq-headers-table.txt'.format(self.gse)))
