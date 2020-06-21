from collections import namedtuple
import logging
import os

import luigi
from luigi.task import getpaths, flatten
from luigi.contrib.external_program import ExternalProgramTask
import requests
from requests.auth import HTTPBasicAuth

from .config import core

cfg = core()
logger = logging.getLogger('luigi-interface')

class IlluminaFastqHeader:
    @classmethod
    def parse(cls, s):
        pieces = s.split(':')
        if len(pieces) == 5:
            device, flowcell_lane, tile, x, y = pieces
            return cls(device, flowcell_lane=flowcell_lane, tile=tile, x=x, y=y)
        elif len(pieces) == 7:
            return cls(*pieces)
        else:
            raise TypeError('Unsupported Illumina FASTQ header format {}.'.format(s))

    def __init__(self, device, run=None, flowcell=None, flowcell_lane=None, tile=None, x=None, y=None):
        self.device = device
        self.run = run
        self.flowcell = flowcell
        self.flowcell_lane = flowcell_lane
        self.tile = tile
        self.x = x
        self.y = y

    def get_batch_factor(self):
        if self.flowcell is None:
            return self.device, self.flowcell_lane
        return self.device, self.flowcell, self.flowcell_lane

def parse_illumina_fastq_header(s):
    return IlluminaFastqHeader(*s.split(':'))

def max_retry(count):
    """
    Set the maximum number of time a task can be retried before being disabled
    as per Luigi retry policy.
    """
    def wrapper(cls):
        cls.retry_count = count
        return cls
    return wrapper

no_retry = max_retry(0)

class TaskWithPriorityMixin:
    """Mixin that adds a --priority flag to a given task."""
    priority = luigi.IntParameter(default=0, positional=False, significant=False)

class RerunnableTaskMixin:
    """
    Mixin for a task that can be rerun regardless of its completion status.
    """
    rerun = luigi.BoolParameter(default=False, positional=False, significant=False)

    def __init__(self, *kwargs, **kwds):
        super().__init__(*kwargs, **kwds)
        self._has_rerun = False

    def run(self):
        try:
            super().run()
        finally:
            self._has_rerun = True

    def complete(self):
        return (not self.rerun or self._has_rerun) and super().complete()

class GemmaTask(ExternalProgramTask):
    """
    Base class for tasks that wraps Gemma CLI.
    """
    experiment_id = luigi.Parameter()

    subcommand = None

    @staticmethod
    def get_reference_id_for_taxon(taxon):
        try:
            return {'human': 'hg38_ncbi', 'mouse': 'mm10_ncbi', 'rat': 'm6_ncbi'}[taxon]
        except KeyError:
            raise ValueError('Unsupported Gemma taxon {}.'.format(taxon))

    def get_dataset_info(self):
        basic_auth = HTTPBasicAuth(os.getenv('GEMMAUSERNAME'), os.getenv('GEMMAPASSWORD'))
        res = requests.get('https://gemma.msl.ubc.ca/rest/v2/datasets/{}'.format(self.experiment_id), auth=basic_auth)
        res.raise_for_status()
        if not res.json()['data']:
            raise RuntimeError('Could not retrieve Gemma dataset with short name {}.'.format(self.experiment_id))
        return res.json()['data'][0]

    def get_taxon(self):
        return self.get_dataset_info()['taxon']

    def get_platform_short_name(self):
        return 'Generic_{}_ncbiIds'.format(self.get_taxon())

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

    def run(self):
        ret = super(GemmaTask, self).run()
        if not self.complete():
            raise RuntimeError('{} is not completed after successful run().'.format(repr(self)))
        return ret
