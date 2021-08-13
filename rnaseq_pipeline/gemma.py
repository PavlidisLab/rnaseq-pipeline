import os
from os.path import join

import luigi
from luigi.contrib.external_program import ExternalProgramTask
import requests
from requests.auth import HTTPBasicAuth

from .config import rnaseq_pipeline

cfg = rnaseq_pipeline()

class GemmaApi:
    _basic_auth = HTTPBasicAuth(os.getenv('GEMMAUSERNAME'),
            os.getenv('GEMMAPASSWORD')) if os.getenv('GEMMAUSERNAME') else None

    def __init__(self, timeout=10):
        self._session = requests.Session()
        self._timeout = timeout

    def _query_api(self, endpoint):
        res = requests.get(join('https://gemma.msl.ubc.ca/rest/v2', endpoint), auth=self._basic_auth, timeout=self._timeout)
        res.raise_for_status()
        return res.json()['data']

    def datasets(self, experiment_id):
        return self._query_api(join('datasets', experiment_id))

    def samples(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'samples'))

    def platforms(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'platforms'))

class GemmaTask(ExternalProgramTask):
    """
    Base class for tasks that wraps Gemma CLI.
    """
    experiment_id = luigi.Parameter()

    subcommand = None

    def __init__(self, *kwargs, **kwds):
        super().__init__(*kwargs, **kwds)
        self._gemma_api = GemmaApi()

    @property
    def dataset_info(self):
        if not hasattr(self, '_dataset_info'):
            data = self._gemma_api.datasets(self.experiment_id)
            if not data:
                raise RuntimeError('Could not retrieve Gemma dataset with short name {}.'.format(self.experiment_id))
            self._dataset_info = data[0]
        return self._dataset_info

    @property
    def dataset_short_name(self):
        return self.dataset_info['shortName']

    @property
    def accession(self):
        return self.dataset_info['accession']

    @property
    def external_database(self):
        return self.dataset_info['externalDatabase']

    @property
    def external_uri(self):
        return self.dataset_info['externalUri']

    @property
    def taxon(self):
        return self.dataset_info['taxon']

    @property
    def reference_id(self):
        try:
            return {'human': 'hg38_ncbi', 'mouse': 'mm10_ncbi', 'rat': 'm6_ncbi'}[self.taxon]
        except KeyError:
            raise ValueError('Unsupported Gemma taxon {}.'.format(self.taxon))

    @property
    def platform_short_name(self):
        return f'Generic_{self.taxon}_ncbiIds'

    def program_environment(self):
        return cfg.asenv(['GEMMA_LIB', 'JAVA_HOME', 'JAVA_OPTS'])

    def program_args(self):
        args = [cfg.GEMMACLI,
                self.subcommand,
                '-u', os.getenv('GEMMAUSERNAME'),
                '-p', os.getenv('GEMMAPASSWORD'),
                '-e', self.experiment_id]
        args.extend(self.subcommand_args())
        return args

    def subcommand_args(self):
        return []

