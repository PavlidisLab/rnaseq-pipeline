"""
This module contains all the logic to retrieve RNA-Seq data from GEO.
"""

import gzip
import logging
import os
import re
import tarfile
import tempfile
from datetime import timedelta
from functools import lru_cache
from os.path import join
from urllib.parse import urlparse, parse_qs
from xml.etree import ElementTree

import luigi
import luigi.format
import requests
from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask, TaskWithMetadataMixin
from luigi.util import requires
from luigi.task import flatten

from .sra import DownloadSraExperiment
from ..config import rnaseq_pipeline
from ..miniml_utils import collect_geo_samples, collect_geo_samples_info
from ..platforms import BgiPlatform, IlluminaPlatform
from ..targets import ExpirableLocalTarget
from ..utils import RerunnableTaskMixin

cfg = rnaseq_pipeline()

logger = logging.getLogger(__name__)

ns = {'miniml': 'http://www.ncbi.nlm.nih.gov/geo/info/MINiML'}

@lru_cache()
def retrieve_geo_platform_miniml(geo_platform):
    """Retrieve a GEO platform MINiML metadata"""
    res = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi', params=dict(acc=geo_platform, form='xml'))
    res.raise_for_status()
    return ElementTree.fromstring(res.text).find('miniml:Platform', ns)

def match_geo_platform(geo_platform):
    """Infer the type of platform given a GEO platform"""
    root = retrieve_geo_platform_miniml(geo_platform)
    geo_platform_title = root.find('miniml:Title', ns).text

    # BGI
    if geo_platform_title.startswith('BGISEQ') or geo_platform_title.startswith('DNBSEQ'):
        return BgiPlatform(geo_platform_title.split(' ')[0])

    # Illumina HiSeq X and NextSeq 550 platforms are not prefixed with Illumina
    illumina_regex = [r'Illumina (.+) \(.+\)', r'(HiSeq X .+) \(.+\)', r'(NextSeq 550) \(.+\)',
                      r'(NextSeq 2000) \(.+\)']

    for r in illumina_regex:
        illumina_match = re.match(r, geo_platform_title)
        if illumina_match:
            return IlluminaPlatform(illumina_match.group(1))

    raise NotImplementedError(f'Unsupported GEO platform: {geo_platform_title} ({geo_platform}).')

class DownloadGeoSampleMetadata(TaskWithMetadataMixin, RerunnableTaskMixin, luigi.Task):
    """
    Download the MiNiML metadata for a given GEO Sample.
    """
    gsm: str = luigi.Parameter()

    resources = {'geo_http_connections': 1}

    retry_count = 3

    def run(self):
        if self.output().is_stale():
            logger.info('%s is stale, redownloading...', self.output())
        res = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi', params=dict(acc=self.gsm, form='xml'))
        res.raise_for_status()
        try:
            ElementTree.fromstring(res.text)
        except ElementTree.ParseError as e:
            raise Exception('Failed to parse XML from GEO sample metadata of ' + self.gsm) from e
        with self.output().open('w') as f:
            f.write(res.text)

    def output(self):
        return ExpirableLocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}.xml'.format(self.gsm)),
                                    ttl=timedelta(days=14))

@requires(DownloadGeoSampleMetadata)
class DownloadGeoSample(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Download a GEO Sample given a runinfo file and
    """
    gsm: str
    metadata: dict

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
        # do not override the sample_id when invoked from DownloadGemmaExperiment
        if 'sample_id' not in metadata:
            metadata['sample_id'] = self.sample_id
        yield DownloadSraExperiment(srx, metadata=metadata)

class DownloadGeoSeriesMetadata(TaskWithMetadataMixin, RerunnableTaskMixin, luigi.Task):
    """
    Download a GEO Series metadata containg information about related GEO
    Samples.
    """
    gse: str = luigi.Parameter()

    resources = {'geo_http_connections': 1}

    retry_count = 3

    def run(self):
        if self.output().is_stale():
            logger.info('%s is stale, redownloading...', self.output())
        res = requests.get('https://ftp.ncbi.nlm.nih.gov/geo/series/' + self.gse[
            :-3] + 'nnn/' + self.gse + '/miniml/' + self.gse + '_family.xml.tgz',
                           stream=True)
        res.raise_for_status()
        # we need to use a temporary file because Response.raw does not allow seeking
        with tempfile.TemporaryFile() as tmp:
            for chunk in res.iter_content(chunk_size=1024):
                tmp.write(chunk)
            tmp.seek(0)
            with tarfile.open(fileobj=tmp, mode='r:gz') as fin, self.output().open('w') as f:
                reader = fin.extractfile(self.gse + '_family.xml')
                while chunk := reader.read(1024):
                    f.write(chunk)

    def output(self):
        # TODO: remove the _family suffix
        return ExpirableLocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}_family.xml'.format(self.gse)),
                                    ttl=timedelta(days=14), format=luigi.format.Nop)

@requires(DownloadGeoSeriesMetadata)
class DownloadGeoSeries(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Download all GEO Samples related to a GEO Series.
    """
    gse: str
    metadata: dict

    ignored_samples = luigi.ListParameter(default=[], description='Ignored GSM identifiers')

    def run(self):
        gsms = collect_geo_samples(self.input().path)
        gsms = [gsm for gsm in gsms if gsm not in self.ignored_samples]
        if not gsms:
            raise ValueError('{} has no related GEO samples with RNA-Seq data.'.format(self.gse))
        yield [DownloadGeoSample(gsm, metadata=self.metadata) for gsm in gsms]

@requires(DownloadGeoSeriesMetadata, DownloadGeoSeries)
class ExtractGeoSeriesBatchInfo(luigi.Task):
    """
    Extract the GEO Series batch information by looking up the GEO Series
    metadata and some downloaded FASTQs headers.
    """
    gse: str

    def run(self):
        geo_series_metadata, samples = self.requires()
        samples = next(samples.run())
        sample_geo_metadata = collect_geo_samples_info(geo_series_metadata.output().path)
        with self.output().open('w') as info_out:
            for sample in samples:
                if len(sample.output()) == 0:
                    logger.warning(
                        'GEO sample %s has no associated FASTQs from which batch information can be extracted.',
                        sample.sample_id)
                    continue

                # TODO: find a cleaner way to obtain the SRA run accession
                for run in flatten(sample.output()):
                    for fastq in run.files:
                        # strip the two extensions (.fastq.gz)
                        fastq_name, _ = os.path.splitext(fastq)
                        fastq_name, _ = os.path.splitext(fastq_name)

                        # is this necessary?
                        fastq_id = os.path.basename(fastq_name)

                        platform_id, srx_uri = sample_geo_metadata[sample.sample_id]

                        with gzip.open(fastq, 'rt') as f:
                            fastq_header = f.readline().rstrip()

                        info_out.write('\t'.join([sample.sample_id, fastq_id, platform_id, srx_uri, fastq_header]) + '\n')

    def output(self):
        # TODO: organize batch info per source
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.BATCHINFODIR, '{}.fastq-headers-table.txt'.format(self.gse)))
