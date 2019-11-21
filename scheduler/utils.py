import luigi

class WrapperTask(luigi.WrapperTask):
    """
    Extension to luigi.WrapperTask to inherit the dependencies outputs as well
    as the completion condition.
    """
    def output(self):
        return luigi.task.getpaths(self.requires())

class NonAtomicTaskRunContext(object):
    """
    Execution context for non-atomic tasks that ensures that any existing
    output is deleted if the task fails.
    """
    def __init__(self, task):
        self.task = task

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            for out in self.task.output():
                if out.exists():
                    out.remove()
