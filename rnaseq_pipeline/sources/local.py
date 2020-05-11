from glob import glob
import os
from os.path import join

from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask
import luigi

from ..config import core

cfg = core()

class DownloadLocalSample(luigi.Task):
    """
    Local samples are organized by :experiment_id: to avoid name clashes across
    experiments.
    """
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    def output(self):
        # we sort to make sure that pair ends are in correct order
        return [luigi.LocalTarget(f) for f in sorted(glob(join(cfg.OUTPUT_DIR, cfg.DATA, 'local', self.experiment_id, self.sample_id, '*.fastq.gz')))]

class DownloadLocalExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    experiment_id = luigi.Parameter()

    def run(self):
        yield [DownloadLocalSample(self.experiment_id, os.path.basename(f))
                for f in glob(join(cfg.OUTPUT_DIR, cfg.DATA, 'local', self.experiment_id, '*'))]
