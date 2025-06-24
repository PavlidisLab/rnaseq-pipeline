import os
from glob import glob
from os.path import join

import luigi
from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask

from ..config import rnaseq_pipeline
from ..platforms import IlluminaPlatform

cfg = rnaseq_pipeline()

class DownloadLocalSample(luigi.Task):
    """
    Local samples are organized by :experiment_id: to avoid name clashes across
    experiments.
    """
    experiment_id: str = luigi.Parameter()
    sample_id: str = luigi.Parameter()

    @property
    def platform(self):
        return IlluminaPlatform('HiSeq 2500')

    def output(self):
        # we sort to make sure that pair ends are in correct order
        return [luigi.LocalTarget(f) for f in
                sorted(glob(join(cfg.OUTPUT_DIR, cfg.DATA, 'local', self.experiment_id, self.sample_id, '*.fastq.gz')))]

class DownloadLocalExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    experiment_id: str = luigi.Parameter()

    def run(self):
        yield [DownloadLocalSample(self.experiment_id, os.path.basename(f))
               for f in glob(join(cfg.OUTPUT_DIR, cfg.DATA, 'local', self.experiment_id, '*'))]
