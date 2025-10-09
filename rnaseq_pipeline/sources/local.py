from glob import glob
from os.path import join, basename

import luigi
from bioluigi.tasks.utils import TaskWithOutputMixin

from ..config import rnaseq_pipeline
from ..platforms import IlluminaPlatform, BgiPlatform, IlluminaNexteraPlatform, TaskWithPlatformMixin

cfg = rnaseq_pipeline()

class DownloadLocalSample(TaskWithPlatformMixin, luigi.Task):
    """
    Local samples are organized by :experiment_id: to avoid name clashes across
    experiments.
    """
    experiment_id: str = luigi.Parameter()
    sample_id: str = luigi.Parameter()

    @property
    def platform(self):
        if self.platform_name == 'ILLUMINA':
            return IlluminaPlatform(self.platform_instrument)
        elif self.platform_name == 'BGI':
            return BgiPlatform(self.platform_instrument)
        elif self.platform_name == 'NEXTERA':
            return IlluminaNexteraPlatform(self.platform_instrument)
        else:
            raise ValueError('Unsupported platform name {}.'.format(self.platform_name))

    def output(self):
        # we sort to make sure that pair ends are in correct order
        return [luigi.LocalTarget(f) for f in
                sorted(glob(join(cfg.OUTPUT_DIR, cfg.DATA, 'local', self.experiment_id, self.sample_id, '*.fastq.gz')))]

class DownloadLocalExperiment(luigi.WrapperTask, TaskWithPlatformMixin, TaskWithOutputMixin):
    experiment_id: str = luigi.Parameter()

    def requires(self):
        yield [DownloadLocalSample(self.experiment_id, basename(f), platform_name=self.platform_name,
                                   platform_instrument=self.platform_instrument)
               for f in glob(join(cfg.OUTPUT_DIR, cfg.DATA, 'local', self.experiment_id, '*'))]
