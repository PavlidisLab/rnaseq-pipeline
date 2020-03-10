from collections import namedtuple
import logging
import os

import luigi
from luigi.task import getpaths, flatten
from luigi.contrib.external_program import ExternalProgramTask
import requests
from requests.auth import HTTPBasicAuth

from .config import rnaseq_pipeline

cfg = rnaseq_pipeline()
logger = logging.getLogger('luigi-interface')


class IlluminaFastqHeader():
    @classmethod
    def parse(cls, s):
        return cls(*s.split(':'))

    def __init__(self, device, run, flowcell, flowcell_lane, tile, x=None, y=None):
        self.device = device
        self.run = run
        self.flowcell = flowcell
        self.flowcell_lane =flowcell_lane
        self.tile = tile
        self.x = x
        self.y = y

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

class WrapperTask(luigi.WrapperTask):
    """
    Extension to luigi.WrapperTask to inherit the dependencies outputs as well
    as the completion condition.
    """
    def output(self):
        return luigi.task.getpaths(self.requires())

class DynamicWrapperTask(luigi.Task):
    """
    Similar to WrapperTask but for dynamic dependencies yielded in the body of
    the run() method.
    """
    def output(self):
        tasks = []
        if all(req.complete() for req in flatten(self.requires())):
            try:
                tasks = list(self.run())
            except:
                logger.exception('%s failed at run() step; the exception will not be raised because Luigi is still building the graph.', repr(self))

        # FIXME: conserve task structure: the generator actually create an
        # implicit array level even if a single task is yielded.
        # For now, we just handle the special singleton case.
        if len(tasks) == 1:
            tasks = tasks[0]

        return getpaths(tasks)

    def complete(self):
        if not all(req.complete() for req in flatten(self.requires())):
            return False
        return super().complete()

class GemmaTask(ExternalProgramTask):
    """
    Base class for tasks that wraps Gemma CLI.
    """
    experiment_id = luigi.Parameter()
    resources = {'gemma_connections': 1}

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
