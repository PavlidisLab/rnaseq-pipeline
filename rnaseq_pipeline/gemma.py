import enum
import logging
import os
import subprocess
from getpass import getpass
from os.path import join
from typing import Optional

import luigi
import requests
from luigi.contrib.external_program import ExternalProgramTask
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

class GemmaConfig(luigi.Config):
    @classmethod
    def get_task_family(cls):
        return 'rnaseq_pipeline.gemma'

    baseurl: str = luigi.Parameter(default='https://gemma.msl.ubc.ca', description='Base URL for Gemma')
    appdata_dir: str = luigi.Parameter(description='Directory where Gemma data is stored')
    cli_bin: str = luigi.Parameter(default='gemma-cli', description='Gemma CLI tool name')
    cli_JAVA_HOME: Optional[str] = luigi.Parameter(default=None, description='Override $JAVA_HOME for the Gemma CLI')
    cli_JAVA_OPTS: Optional[str] = luigi.Parameter(default=None, description='Override $JAVA_OPTS for the Gemma CLI')
    human_reference_id: str = luigi.Parameter()
    mouse_reference_id: str = luigi.Parameter()
    rat_reference_id: str = luigi.Parameter()
    human_single_cell_reference_id: str = luigi.Parameter()
    mouse_single_cell_reference_id: str = luigi.Parameter()
    rat_single_cell_reference_id: str = luigi.Parameter()

cfg = GemmaConfig()

class GemmaApi:
    def __init__(self):
        self._auth = HTTPBasicAuth(os.getenv('GEMMA_USERNAME'), self._get_password()) if os.getenv(
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
        res = requests.get(join(cfg.baseurl, 'rest/v2', endpoint), auth=self._auth)
        res.raise_for_status()
        return res.json()['data']

    def datasets(self, experiment_id):
        return self._query_api(join('datasets', experiment_id))

    def dataset_annotations(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'annotations'))

    def dataset_has_batch(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'hasbatch'))

    def samples(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'samples'))

    def platforms(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'platforms'))

    def quantitation_types(self, experiment_id):
        return self._query_api(join('datasets', experiment_id, 'quantitationTypes'))

gemma_api = GemmaApi()

class GemmaTaskMixin(luigi.Task):
    experiment_id = luigi.Parameter()

    @property
    def dataset_info(self):
        if not hasattr(self, '_dataset_info'):
            data = gemma_api.datasets(self.experiment_id)
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
            if self.assay_type == GemmaAssayType.BULK_RNA_SEQ:
                return {'human': cfg.human_reference_id, 'mouse': cfg.mouse_reference_id, 'rat': cfg.rat_reference_id}[
                    self.taxon]
            elif self.assay_type == GemmaAssayType.SINGLE_CELL_RNA_SEQ:
                return {'human': cfg.human_single_cell_reference_id, 'mouse': cfg.mouse_single_cell_reference_id,
                        'rat': cfg.rat_single_cell_reference_id}[
                    self.taxon]
            else:
                raise NotImplementedError
        except KeyError:
            raise ValueError('Unsupported Gemma taxon {}.'.format(self.taxon))

    @property
    def platform_short_name(self):
        return f'Generic_{self.taxon}_ncbiIds'

    @property
    def assay_type(self):
        # Possible values:
        # bulk RNA-seq assay	http://purl.obolibrary.org/obo/OBI_0003090	11345
        # transcription profiling by array assay	http://purl.obolibrary.org/obo/OBI_0001463	10788
        # transcription profiling by high throughput sequencing	http://www.ebi.ac.uk/efo/EFO_0002770	262
        # single-cell RNA sequencing assay	http://purl.obolibrary.org/obo/OBI_0002631	248
        # single-nucleus RNA sequencing assay	http://purl.obolibrary.org/obo/OBI_0003109	150
        # transcription profiling by array	http://www.ebi.ac.uk/efo/EFO_0002768	79
        # single-cell RNA sequencing	http://www.ebi.ac.uk/efo/EFO_0008913	5
        # single nucleus RNA sequencing	http://www.ebi.ac.uk/efo/EFO_0009809	4
        # fluorescence-activated cell sorting	http://www.ebi.ac.uk/efo/EFO_0009108	2
        # RIP-seq	http://www.ebi.ac.uk/efo/EFO_0005310	1
        # RNA-seq of coding RNA from single cells	http://www.ebi.ac.uk/efo/EFO_0005684	0
        # These were pulled from Gemma on October 1st, 2025

        assay_type_class_uri = 'http://purl.obolibrary.org/obo/OBI_0000070'
        microarray_uris = ['http://purl.obolibrary.org/obo/OBI_0001463', 'http://www.ebi.ac.uk/efo/EFO_0002768']
        bulk_rnaseq_uris = ['http://purl.obolibrary.org/obo/OBI_0003090']
        sc_rnaseq_uris = ['http://purl.obolibrary.org/obo/OBI_0002631', 'http://www.ebi.ac.uk/efo/EFO_0008913',
                          'http://www.ebi.ac.uk/efo/EFO_0009809', 'http://purl.obolibrary.org/obo/OBI_0003109',
                          'http://www.ebi.ac.uk/efo/EFO_0005684']
        fac_sorted_uri = 'http://www.ebi.ac.uk/efo/EFO_0009108'

        annotations = gemma_api.dataset_annotations(self.experiment_id)
        fac_sorted = any(annotation['classUri'] == assay_type_class_uri and annotation['termUri'] == fac_sorted_uri
                         for annotation in annotations)
        for annotation in annotations:
            if annotation['classUri'] == assay_type_class_uri:
                value_uri = annotation['termUri']
                if value_uri in microarray_uris:
                    return GemmaAssayType.MICROARRAY
                elif value_uri in bulk_rnaseq_uris:
                    return GemmaAssayType.BULK_RNA_SEQ
                elif value_uri in sc_rnaseq_uris:
                    if fac_sorted:
                        # fac-sorted scRNA-Seq is treated as bulk
                        logger.info('%s: Dataset is a FAC-sorted single-cell RNA-Seq, will treat as bulk RNA-Seq.',
                                    self.dataset_short_name)
                        return GemmaAssayType.BULK_RNA_SEQ
                    else:
                        return GemmaAssayType.SINGLE_CELL_RNA_SEQ

        raise ValueError('No suitable experiment tag to determine the assay type .')

class GemmaAssayType(enum.Enum):
    MICROARRAY = 0
    BULK_RNA_SEQ = 1
    SINGLE_CELL_RNA_SEQ = 2

class GemmaCliTask(GemmaTaskMixin, ExternalProgramTask):
    """
    Base class for tasks that wraps Gemma CLI.
    """
    subcommand = None

    def program_environment(self):
        env = super().program_environment()
        if cfg.cli_JAVA_HOME:
            env['JAVA_HOME'] = cfg.cli_JAVA_HOME
        if cfg.cli_JAVA_OPTS:
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
