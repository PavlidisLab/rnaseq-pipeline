import os

import luigi
import requests
from requests.auth import HTTPBasicAuth

class RsemReference(luigi.Target):
    """
    Represents the target of rsem-prepare-reference script.
    """
    def __init__(self, path):
        self.path = path

    def exists(self):
        exts = ['grp', 'ti', 'seq', 'chrlist']
        return all(os.path.exists(self.path + '.' + ext) for ext in exts)

class GemmaDatasetHasPlatform(luigi.Target):
    """
    This target determines if a Gemma dataset, identified by a short name
    effectively has a platform associated.
    """

    def __init__(self, dataset_short_name, platform):
        self.dataset_short_name = dataset_short_name
        self.platform = platform

    def exists(self):
        basic_auth = HTTPBasicAuth(os.getenv('GEMMAUSERNAME'), os.getenv('GEMMAPASSWORD'))
        res = requests.get('https://gemma.msl.ubc.ca/rest/v2/datasets/{}/platforms'.format(self.dataset_short_name), auth=basic_auth)
        res.raise_for_status()
        return any(platform['shortName'] == self.platform
                   for platform in res.json()['data'])

    def __repr__(self):
        return 'GemmaDatasetHasPlatform(dataset_short_name={}, platform={})'.format(self.dataset_short_name, self.platform)
