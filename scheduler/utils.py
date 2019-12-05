import luigi

class WrapperTask(luigi.WrapperTask):
    """
    Extension to luigi.WrapperTask to inherit the dependencies outputs as well
    as the completion condition.
    """
    def output(self):
        return luigi.task.getpaths(self.requires())

class DynamicWrapperTask(luigi.Task):
    def output(self):
        return [task.output() for task in next(self.run())]
