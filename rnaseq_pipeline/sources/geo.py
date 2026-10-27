"""
This module contains all the logic to retrieve RNA-Seq data from GEO.
"""

import gzip
import json
import logging
import os
import re
import tarfile
import tempfile
import time
from datetime import timedelta
from functools import lru_cache
from os.path import join

import luigi
import luigi.format
import requests
from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask, TaskWithMetadataMixin
from luigi.util import requires
from luigi.task import flatten

from .sra import DownloadSraExperiment
from ..config import Config
from ..miniml_utils import collect_geo_samples, collect_geo_samples_info
from ..platforms import BgiPlatform, IlluminaPlatform
from ..targets import ExpirableLocalTarget
from ..utils import RerunnableTaskMixin

cfg = Config()

logger = logging.getLogger(__name__)


EUTILS_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'

def _eutils_params(**params):
    """Add the NCBI API key from the environment (the same variable EDirect reads) when it is set."""
    api_key = os.environ.get('NCBI_API_KEY')
    if api_key:
        params['api_key'] = api_key
    return params

#: Entrez answers 429 above 3 requests/s without an API key (10/s with one); several tasks share that budget, so a
#: 429 is retried a few times with a growing delay rather than failing the task outright
EUTILS_RATE_LIMIT_RETRIES = 3

def _eutils_get(endpoint, **params):
    params = _eutils_params(retmode='json', **params)
    for attempt in range(EUTILS_RATE_LIMIT_RETRIES + 1):
        res = requests.get(EUTILS_URL + '/' + endpoint, params=params)
        if res.status_code != 429 or attempt == EUTILS_RATE_LIMIT_RETRIES:
            break
        delay = float(res.headers.get('Retry-After') or 2 ** attempt)
        logger.info('Entrez %s is rate-limited, retrying in %.0f s...', endpoint, delay)
        time.sleep(delay)
    # Errors are raised by hand rather than with raise_for_status(): the request URL carries the API key, and
    # requests puts the full URL in its error message (and Entrez echoes the key back in its error body).
    body = res.text
    if 'api_key' in params:
        body = body.replace(params['api_key'], '<NCBI_API_KEY>')
    if res.status_code != 200:
        hint = ' (NCBI rejected the API key in NCBI_API_KEY)' if 'API key status invalid' in body else ''
        raise RuntimeError(f'Entrez {endpoint} answered HTTP {res.status_code}{hint}: {body[:300]}')
    payload = res.json()
    # Entrez reports some failures (e.g. "API rate limit exceeded") in the body of a 200 response
    if 'error' in payload:
        raise RuntimeError(f'Entrez {endpoint} failed: {body[:300]}')
    return payload

def retrieve_geo_summary(accession, entry_type):
    """
    Retrieve the Entrez summary of a GEO record (db=gds).

    GEO's acc.cgi pages are served behind a reCAPTCHA challenge (an HTML page with HTTP 200) unless the request
    carries a particular set of parameters, and that set has changed over time. Entrez is the supported API: it is
    not challenged, takes an API key and publishes its rate limits.

    :param accession: a GEO accession (e.g. GSM9939224 or GPL24676)
    :param entry_type: the GEO entry type to search (gsm, gpl, gse); without it, searching a platform accession also
    returns every series that uses it
    """
    search = _eutils_get('esearch.fcgi', db='gds', term=f'{accession}[ACCN] AND {entry_type}[ETYP]')
    uids = search['esearchresult']['idlist']
    if not uids:
        raise ValueError(f'No GEO record found for {accession} (Entrez db=gds, entry type {entry_type}).')
    summary = _eutils_get('esummary.fcgi', db='gds', id=','.join(uids))['result']
    for uid in summary['uids']:
        if summary[uid].get('accession') == accession:
            return summary[uid]
    raise ValueError(f'Entrez returned no summary for {accession} among {uids}.')

@lru_cache()
def retrieve_geo_platform_title(geo_platform):
    """Retrieve the title of a GEO platform"""
    return retrieve_geo_summary(geo_platform, 'gpl')['title']

def match_geo_platform(geo_platform):
    """Infer the type of platform given a GEO platform"""
    geo_platform_title = retrieve_geo_platform_title(geo_platform)

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
    Download the Entrez summary (db=gds) for a given GEO Sample.

    The summary carries the sample's platform and its SRA link, which is all DownloadGeoSample needs.
    """
    gsm: str = luigi.Parameter()

    resources = {'edirect_http_connections': 1}

    retry_count = 3

    def run(self):
        if self.output().is_stale():
            logger.info('%s is stale, redownloading...', self.output())
        summary = retrieve_geo_summary(self.gsm, 'gsm')
        with self.output().open('w') as f:
            json.dump(summary, f)

    def output(self):
        return ExpirableLocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'geo', '{}.json'.format(self.gsm)),
                                    ttl=timedelta(days=14))

def read_geo_sample_info(path):
    """
    Read the platform and SRA experiment of a GEO sample from its Entrez summary.

    :return: a (platform, SRX accession) tuple, or None if the sample is not linked to SRA
    """
    with open(path) as f:
        summary = json.load(f)
    srx = next((r['targetobject'] for r in summary.get('extrelations') or []
                if r.get('relationtype') == 'SRA'), None)
    if srx is None:
        return None
    return 'GPL' + summary['gpl'], srx

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
        sample_info = read_geo_sample_info(self.input().path)
        if sample_info is None:
            raise RuntimeError('{} GEO record is not linked to SRA.'.format(self.gsm))
        geo_platform, _ = sample_info
        return match_geo_platform(geo_platform)

    def run(self):
        sample_info = read_geo_sample_info(self.input().path)
        if sample_info is None:
            raise RuntimeError('{} GEO record is not linked to SRA.'.format(self.gsm))
        platform, srx = sample_info
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
