import os

import luigi
import requests
from requests.auth import HTTPBasicAuth

from geo import DownloadGeoSample
from ..utils import WrapperTask

class DownloadGemmaExperiment(WrapperTask):
    """
    Download an experiment described by a Gemma dataset using the REST API.

    Gemma itself does not retain raw data, so this task delegate the work to
    other sources.
    """
    experiment_id = luigi.Parameter()

    def requires(self):
        res = requests.get('http://gemma.msl.ubc.ca/rest/v2/datasets/{}/samples'.format(self.experiment_id), auth=HTTPBasicAuth(os.getenv('GEMMAUSERNAME'), os.getenv('GEMMAPASSWORD')))
        res.raise_for_status()
        return [DownloadGeoSample(sample['accession']['accession'])
                for sample in res.json()['data'] if sample['accession']['externalDatabase']['name'] == 'GEO']
