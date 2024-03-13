"""
This module contains all the logic to retrieve RNA-Seq data from GEO.
"""

from datetime import timedelta
import gzip
import logging
from subprocess import Popen
import os
from os.path import join
from urllib.parse import urlparse, parse_qs
from functools import lru_cache
import re
import requests
import xml.etree.ElementTree

from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask, TaskWithMetadataMixin
import luigi
from luigi.util import requires
import requests

from ..config import rnaseq_pipeline
from ..miniml_utils import collect_geo_samples, collect_geo_samples_info
from ..platforms import Platform, BgiPlatform, IlluminaPlatform
from ..targets import ExpirableLocalTarget
from ..utils import RerunnableTaskMixin
from .sra import DownloadSraExperiment

cfg = rnaseq_pipeline()

logger = logging.getLogger('luigi-interface')

ns = {'miniml': 'http://www.ncbi.nlm.nih.gov/geo/info/MINiML'}

@lru_cache()
def retrieve_geo_platform_miniml(geo_platform):
    """Retrieve a GEO platform MINiML metadata"""
    res = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi', params=dict(acc=geo_platform, form='xml'))
    res.raise_for_status()
    return xml.etree.ElementTree.fromstring(res.text).find('miniml:Platform', ns)

def match_geo_platform(geo_platform):
    """Infer the type of platform given a GEO platform"""
    root = retrieve_geo_platform_miniml(geo_platform)
    geo_platform_title = root.find('miniml:Title', ns).text

    # BGI
    if geo_platform_title.startswith('BGISEQ') or geo_platform_title.startswith('DNBSEQ'):
        return BgiPlatform(geo_platform_title.split(' ')[0])

    # Illumina HiSeq X and NextSeq 550 platforms are not prefixed with Illumina
    illumina_regex = [r'Illumina (.+) \(.+\)', r'(HiSeq X .+) \(.+\)', r'(NextSeq 550) \(.+\)', r'(NextSeq 2000) \(.+\)']

    for r in illumina_regex:
        illumina_match = re.match(r, geo_platform_title)
        if illumina_match:
            return IlluminaPlatform(illumina_match.group(1))

    raise NotImplementedError(f'Unsupported GEO platform: {geo_platform_title} ({geo_platform}).')

class DownloadGeoSampleMetadata(TaskWithMetadataMixin, RerunnableTaskMixin, luigi.Task):
    """
    Download the MiNiML metadata for a given GEO Sample.
    """
    gsm = luigi.Parameter()

    resources = {'geo_http_connections': 1}

    retry_count = 3

    def run(self):
        if self.output().is_stale():
            logger.info('%s is stale, redownloading...', self.output())
        res = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi', params=dict(acc=self.gsm, form='xml'))
        res.raise_for_status()
        with self.output().open('w') as f:
            f.write(res.text)

    def output(self):
        return ExpirableLocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}.xml'.format(self.gsm)), ttl=timedelta(days=14))

@requires(DownloadGeoSampleMetadata)
class DownloadGeoSample(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Download a GEO Sample given a runinfo file and
    """

    @property
    def sample_id(self):
        return self.gsm

    @property
    def platform(self):
        samples_info = collect_geo_samples_info(self.input().path)
        if not self.gsm in samples_info:
            raise RuntimeError('{} GEO record is not linked to SRA.'.format(self.gsm))
        geo_platform, _ = samples_info[self.gsm]
        return match_geo_platform(geo_platform)

    def run(self):
        samples_info = collect_geo_samples_info(self.input().path)
        if not self.gsm in samples_info:
            raise RuntimeError('{} GEO record is not linked to SRA.'.format(self.gsm))
        platform, srx_url = samples_info[self.gsm]
        srx = parse_qs(urlparse(srx_url).query)['term'][0]
        metadata = dict(self.metadata)
        metadata['sample_id'] = self.sample_id
        yield DownloadSraExperiment(srx, metadata=metadata)

class DownloadGeoSeriesMetadata(TaskWithMetadataMixin, RerunnableTaskMixin, luigi.Task):
    """
    Download a GEO Series metadata containg information about related GEO
    Samples.
    """
    gse = luigi.Parameter()

    resources = {'geo_http_connections': 1}

    retry_count = 3

    def run(self):
        if self.output().is_stale():
            logger.info('%s is stale, redownloading...', self.output())
        res = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi', params=dict(acc=self.gse, form='xml', targ='gsm'))
        res.raise_for_status()
        with self.output().open('w') as f:
            f.write(res.text)

    def output(self):
        # TODO: remove the _family suffix
        return ExpirableLocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}_family.xml'.format(self.gse)), ttl=timedelta(days=14))

@requires(DownloadGeoSeriesMetadata)
class DownloadGeoSeries(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Download all GEO Samples related to a GEO Series.
    """

    def run(self):
        gsms = collect_geo_samples(self.input().path)
        if not gsms:
            raise ValueError('{} has no related GEO samples with RNA-Seq data.'.format(self.gse))
        yield [DownloadGeoSample(gsm, metadata=self.metadata) for gsm in gsms]

@requires(DownloadGeoSeriesMetadata, DownloadGeoSeries)
class ExtractGeoSeriesBatchInfo(luigi.Task):
    """
    Extract the GEO Series batch information by looking up the GEO Series
    metadata and some downloaded FASTQs headers.
    """

    def run(self):
        geo_series_metadata, samples = self.requires()
        samples = next(samples.run())
        sample_geo_metadata = collect_geo_samples_info(geo_series_metadata.output().path)
        with self.output().open('w') as info_out:
            for sample in samples:
                if len(sample.output()) == 0:
                    logger.warning('GEO sample %s has no associated FASTQs from which batch information can be extracted.', sample.sample_id)
                    continue

                # TODO: find a cleaner way to obtain the SRA run accession
                for fastq in sample.output():
                    # strip the two extensions (.fastq.gz)
                    fastq_name, _ = os.path.splitext(fastq.path)
                    fastq_name, _ = os.path.splitext(fastq_name)

                    # is this necessary?
                    fastq_id = os.path.basename(fastq_name)

                    platform_id, srx_uri = sample_geo_metadata[sample.sample_id]

                    with gzip.open(fastq.path, 'rt') as f:
                        fastq_header = f.readline().rstrip()

                    info_out.write('\t'.join([sample.sample_id, fastq_id, platform_id, srx_uri, fastq_header]) + '\n')

    def output(self):
        # TODO: organize batch info per source
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.BATCHINFODIR, '{}.fastq-headers-table.txt'.format(self.gse)))
