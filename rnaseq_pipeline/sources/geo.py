import gzip
import logging
from subprocess import Popen, check_call, PIPE
import os
from os.path import join
import urllib
from urlparse import urlparse, parse_qs
import tarfile

import luigi
from luigi.util import requires
import pandas as pd
import requests

from ..config import rnaseq_pipeline
from ..miniml_utils import collect_geo_samples_with_rnaseq_data, collect_geo_samples_info
from ..utils import DynamicWrapperTask
from .sra import DownloadSraExperiment

"""
This module contains all the logic to retrieve RNA-Seq data from GEO.
"""

cfg = rnaseq_pipeline()

logger = logging.getLogger('luigi-interface')

class DownloadGeoSampleMetadata(luigi.Task):
    """
    Download the MiNiML metadata for a given GEO Sample.
    """
    gsm = luigi.Parameter()

    def run(self):
        res = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi', params=dict(acc=self.gsm, form='xml'))
        res.raise_for_status()
        with self.output().open('w') as f:
            f.write(res.content)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}.xml'.format(self.gsm)))

@requires(DownloadGeoSampleMetadata)
class DownloadGeoSample(DynamicWrapperTask):
    """
    Download a GEO Sample given a runinfo file and
    """

    @property
    def sample_id(self):
        return self.gsm

    def run(self):
        samples_info = collect_geo_samples_info(self.input().path)
        platform, srx_url = samples_info[self.gsm]
        srx = parse_qs(urlparse(srx_url).query)['term'][0]
        yield DownloadSraExperiment(srx)

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
