import os
from os.path import join, exists

import luigi
import requests
from requests.auth import HTTPBasicAuth
from .gemma import GemmaApi

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

class GemmaDatasetPlatform(luigi.Target):
    """
    Represents a platform associated to a Gemma dataset.
    """

    def __init__(self, dataset_short_name, platform):
        self.dataset_short_name = dataset_short_name
        self.platform = platform
        self._gemma_api = GemmaApi()

    def exists(self):
        # any platform associated must match
        return any(platform['shortName'] == self.platform
                   for platform in self._gemma_api.platforms(self.dataset_short_name))

    def __repr__(self):
        return 'GemmaDatasetPlatform(dataset_short_name={}, platform={})'.format(self.dataset_short_name, self.platform)

class GemmaDatasetFactor(luigi.Target):
    """
    Represents a batch info factor associated to a Gemma dataset.
    """
    def __init__(self, dataset_short_name, factor):
        self.dataset_short_name = dataset_short_name
        self.factor = factor
        self._gemma_api = GemmaApi()

    def exists(self):
        # all samples must have a batch factor
        return all(self.factor in sample['sample']['factors'].values()
            for sample in self._gemma_api.samples(self.dataset_short_name))
