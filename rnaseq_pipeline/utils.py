import logging

import luigi
from luigi.task import flatten_output

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

    @property
    def batch_factor(self):
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
            return super().run()
        finally:
            self._has_rerun = True

    def complete(self):
        return (not self.rerun or self._has_rerun) and super().complete()

class CheckAfterCompleteMixin:
    """Ensures that a task is completed after a successful run()."""
    def run(self):
        ret = super().run()
        if not self.complete():
            raise RuntimeError('{} is not completed after successful run().'.format(repr(self)))
        return ret

def remove_task_output(task):
    logger.info('Cleaning up %s...', repr(task))
    for out in flatten_output(task):
        if hasattr(out, 'remove') and out.exists():
            try:
                out.remove()
                logger.info('Removed %s.', repr(out))
            except:
                logger.exception('Failed to remove %s.', repr(out))
