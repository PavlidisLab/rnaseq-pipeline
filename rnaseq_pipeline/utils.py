import logging

import luigi
from luigi.task import flatten_output

logger = logging.getLogger(__name__)

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

class RerunnableTaskMixin(luigi.Task):
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

def remove_task_output(task):
    logger.info('Cleaning up %s...', repr(task))
    for out in flatten_output(task):
        if hasattr(out, 'remove') and out.exists():
            try:
                out.remove()
                logger.info('Removed %s.', repr(out))
            except:
                logger.exception('Failed to remove %s.', repr(out))
