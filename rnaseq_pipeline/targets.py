import os
from os.path import join, exists

import luigi
import requests
from requests.auth import HTTPBasicAuth

class RsemReference(luigi.Target):
    """
    Represents the target of rsem-prepare-reference script.
    """
    def __init__(self, prefix, taxon):
        self.prefix = prefix
        self.taxon = taxon

    def exists(self):
        exts = ['grp', 'ti', 'seq', 'chrlist']
        return all(exists(join(self.prefix, '{}_0.{}'.format(self.taxon, ext)))
                for ext in exts)

def _query_gemma_api(endpoint):
    basic_auth = HTTPBasicAuth(os.getenv('GEMMAUSERNAME'), os.getenv('GEMMAPASSWORD'))
    res = requests.get(join('https://gemma.msl.ubc.ca/rest/v2', endpoint), auth=basic_auth) #/datasets/{}/platforms'.format(self.dataset_short_name), auth=basic_auth)
    res.raise_for_status()
    return res.json()

class GemmaDatasetPlatform(luigi.Target):
    """
    Represents a platform associated to a Gemma dataset.
    """

    def __init__(self, dataset_short_name, platform):
        self.dataset_short_name = dataset_short_name
        self.platform = platform

    def exists(self):
        # any platform associated must match
        return any(platform['shortName'] == self.platform
                   for platform in _query_gemma_api(join('datasets', self.dataset_short_name, 'platforms'))['data'])

    def __repr__(self):
        return 'GemmaDatasetPlatform(dataset_short_name={}, platform={})'.format(self.dataset_short_name, self.platform)

class GemmaDatasetFactor(luigi.Target):
    """
    Represents a batch info factor associated to a Gemma dataset.
    """
    def __init__(self, dataset_short_name, factor):
        self.dataset_short_name = dataset_short_name
        self.factor = factor

    def exists(self):
        # all samples must have a batch factor
        return all(self.factor in sample['sample']['factors'].values()
            for sample in _query_gemma_api(join('datasets', self.dataset_short_name, 'samples'))['data'])
