from abc import abstractmethod
from functools import lru_cache
import re
import requests
import xml.etree.ElementTree

from bioluigi.tasks import cutadapt

ns = {'miniml': 'http://www.ncbi.nlm.nih.gov/geo/info/MINiML'}

class Platform:
    """
    :param name: Platform common name
    """
    name = None

    @staticmethod
    @lru_cache()
    def _retrieve_geo_platform_xml(geo_platform):
        res = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi', params=dict(acc=geo_platform, form='xml'))
        res.raise_for_status()
        return xml.etree.ElementTree.fromstring(res.text).find('miniml:Platform', ns)

    @classmethod
    def from_geo_platform(cls, geo_platform):
        # fetch the platform
        for c in cls.__subclasses__():
            if c.match_geo_platform(geo_platform):
                return c.match_geo_platform(geo_platform)
        raise NotImplementedError(f'GEO platform {geo_platform} is not supported.')

    @abstractmethod
    def get_trim_single_end_reads_task(r1, dest, **kwargs):
        pass

    @abstractmethod
    def get_trim_paired_reads_task(r1,r2, r1_dest, r2_dest, **kwargs):
        pass

class BgiPlatform(Platform):
    # http://seqanswers.com/forums/showthread.php?t=87647 led to a document
    # from BGI mentioning to the following sequences:
    FORWARD_FILTER = 'AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA'
    REVERSE_FILTER = 'AAGTCGGATCGTAGCCATGTCGTTCTGTGAGCCAAGGAGTTG'

    name = 'BGI'

    @classmethod
    def match_geo_platform(cls, geo_platform):
        root = cls._retrieve_geo_platform_xml(geo_platform)
        geo_platform_title = root.find('miniml:Title', ns).text
        if geo_platform_title.startswith('BGISEQ'):
            return cls(geo_platform_title.split(' ')[0])

    def __init__(self, instrument):
        self.instrument = instrument

    def get_trim_single_end_reads_task(self, r1, dest, **kwargs):
        return cutadapt.TrimReads(
                r1,
                dest,
                adapter_3prime=BgiPlatform.FORWARD_FILTER,
                **kwargs)

    def get_trim_paired_reads_task(self, r1, r2, r1_dest, r2_dest, **kwargs):
        return cutadapt.TrimPairedReads(
                r1, r2,
                r1_dest, r2_dest,
                adapter_3prime=BgiPlatform.FORWARD_FILTER,
                reverse_adapter_3prime=BgiPlatform.REVERSE_FILTER,
                **kwargs)
        raise NotImplementedError('Trimming paired reads is not supported for this platform.')

class IlluminaPlatform(Platform):
    UNIVERSAL_ADAPTER = 'AGATCGGAAGAGC'

    name = 'Illumina'

    @classmethod
    def match_geo_platform(cls, geo_platform):
        root = cls._retrieve_geo_platform_xml(geo_platform)
        geo_platform_title = root.find('miniml:Title', ns).text
        m = re.match(r'Illumina (.+) \(.+\)', geo_platform_title)
        if m:
            return cls(m.group(1))

    def __init__(self, instrument):
        self.instrument = instrument

    def get_trim_single_end_reads_task(self, r1, dest, **kwargs):
        return cutadapt.TrimReads(
                r1,
                dest,
                adapter_3prime=IlluminaPlatform.UNIVERSAL_ADAPTER,
                **kwargs)

    def get_trim_paired_reads_task(self, r1, r2, r1_dest, r2_dest, **kwargs):
        return cutadapt.TrimPairedReads(
                r1, r2,
                r1_dest, r2_dest,
                adapter_3prime=IlluminaPlatform.UNIVERSAL_ADAPTER,
                reverse_adapter_3prime=IlluminaPlatform.UNIVERSAL_ADAPTER,
                **kwargs)
