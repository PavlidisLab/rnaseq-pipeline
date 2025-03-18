import os
import subprocess
from getpass import getpass
from os.path import join

import luigi
import requests
from luigi.contrib.external_program import ExternalProgramTask
from requests.auth import HTTPBasicAuth

class gemma(luigi.Config):
    task_namespace = 'rnaseq_pipeline'
    baseurl = luigi.Parameter()
    appdata_dir = luigi.Parameter()
    cli_bin = luigi.Parameter()
    cli_JAVA_HOME = luigi.Parameter()
    cli_JAVA_OPTS = luigi.Parameter()
    human_reference_id = luigi.Parameter()
    mouse_reference_id = luigi.Parameter()
    rat_reference_id = luigi.Parameter()

cfg = gemma()

class GemmaApi:
    def __init__(self):
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(os.getenv('GEMMA_USERNAME'), self._get_password()) if os.getenv(
            'GEMMA_USERNAME') else None

    def _get_password(self):
        if 'GEMMA_PASSWORD' in os.environ:
            return os.environ['GEMMA_PASSWORD']
        elif 'GEMMA_PASSWORD_CMD' in os.environ:
            proc = subprocess.run(os.environ['GEMMA_PASSWORD_CMD'], shell=True, check=True, text=True,
                                  stdout=subprocess.PIPE)
            return proc.stdout.splitlines()[0]
        else:
            return getpass()

    def _query_api(self, endpoint):
        res = self._session.get(join(cfg.baseurl, 'rest/v2', endpoint))
        res.raise_for_status()
        return res.json()['data']

    def datasets(self, experiment_id):
        return self._query_api(join('datasets', experiment_id))

    def dataset_has_batch(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'hasbatch'))

    def samples(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'samples'))

    def platforms(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'platforms'))

class GemmaTaskMixin:
    experiment_id = luigi.Parameter()

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
        return self.dataset_info['taxon']['commonName']

    @property
    def reference_id(self):
        try:
            return {'human': cfg.human_reference_id, 'mouse': cfg.mouse_reference_id, 'rat': cfg.rat_reference_id}[
                self.taxon]
        except KeyError:
            raise ValueError('Unsupported Gemma taxon {}.'.format(self.taxon))

    @property
    def platform_short_name(self):
        return f'Generic_{self.taxon}_ncbiIds'

class GemmaCliTask(GemmaTaskMixin, ExternalProgramTask):
    """
    Base class for tasks that wraps Gemma CLI.
    """
    subcommand = None

    def program_environment(self):
        env = super().program_environment()
        env['JAVA_HOME'] = cfg.cli_JAVA_HOME
        env['JAVA_OPTS'] = cfg.cli_JAVA_OPTS
        return env

    def program_args(self):
        args = [cfg.cli_bin,
                self.subcommand,
                '-e', self.experiment_id]
        args.extend(self.subcommand_args())
        return args

    def subcommand_args(self):
        return []
