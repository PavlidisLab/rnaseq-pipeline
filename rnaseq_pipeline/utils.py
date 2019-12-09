import logging

import luigi
from luigi.task import getpaths, flatten

logger = logging.getLogger('luigi-interface')

class WrapperTask(luigi.WrapperTask):
    """
    Extension to luigi.WrapperTask to inherit the dependencies outputs as well
    as the completion condition.
    """
    def output(self):
        return luigi.task.getpaths(self.requires())

class DynamicWrapperTask(luigi.Task):
    """
    Similar to WrapperTask but for dynamic dependencies.
    """
    def output(self):
        tasks = []
        if all(req.complete() for req in flatten(self.requires())):
            try:
                tasks = list(self.run())
            except Exception as e:
                logger.exception('%s failed at run() step.', repr(self))

        # FIXME: conserve task structure: the generator actually create an
        # implicit array level even if a single task is yielded.
        # For now, we just handle the special singleton case.
        if len(tasks) == 1:
            tasks = tasks[0]

        return getpaths(tasks)
