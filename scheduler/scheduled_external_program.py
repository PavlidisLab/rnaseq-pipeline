import luigi
from luigi.contrib.external_program import ExternalProgramTask, ExternalProgramRunError
from subprocess import Popen, PIPE, check_call
import os
import datetime
import logging

logger = logging.getLogger('luigi-interface')

class Scheduler(object):
    @classmethod
    def fromblurb(cls, blurb):
        for subcls in cls.__subclasses__():
            if subcls.blurb == blurb:
                return subcls()
        else:
            raise ValueError('{} is not a reckognized scheduler.'.format(blurb))

    @classmethod
    def run(self, task):
        raise NotImplemented

class LocalScheduler(Scheduler):
    blurb = 'local'
    @classmethod
    def run(self, task):
        args = list(map(str, task.program_args()))
        env = task.program_environment()
        logger.info('Running command {}'.format(' '.join(args)))
        proc = Popen(args, env=env, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise ExternalProgramRunError('Program exited with non-zero return code.', args, env, stdout, stderr)
        if task.capture_output:
            logger.info('Program stdout:\n{}'.format(stdout))
            logger.info('Program stderr:\n{}'.format(stderr))

class SlurmScheduler(Scheduler):
    blurb = 'slurm'
    @classmethod
    def run(self, task):
        srun_args = [
            '--time', '{}:{}:{}'.format(task.walltime.seconds % 3600, (task.walltime.seconds // 3600) % 60, ((task.walltime.seconds // 3600) // 60)),
            '--mem', '{}M'.format(task.memory),
            '--cpus-per-task', str(task.ncpus)]
        args = list(map(str, task.program_args()))
        env = task.program_environment()
        logger.info('Running command {}'.format(' '.join(args)))
        proc = Popen(['srun'] + srun_args + args, env=env, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise ExternalProgramRunError('Program exited with non-zero return code.', args, env, stdout, stderr)
        if task.capture_output:
            logger.info('Program stdout:\n{}'.format(stdout))
            logger.info('Program stderr:\n{}'.format(stderr))

class ScheduledExternalProgramTask(ExternalProgramTask):
    """
    Variant of luigi.contrib.external_program.ExternalProgramTask that runs on
    a job scheduler.
    """
    walltime = luigi.TimeDeltaParameter(default=datetime.timedelta(hours=1))
    ncpus = luigi.IntParameter(default=1)
    memory = luigi.FloatParameter(default=1024)

    scheduler = luigi.ChoiceParameter(choices=[cls.blurb for cls in Scheduler.__subclasses__()], default='local')

    def run(self):
        return Scheduler.fromblurb(self.scheduler).run(self)
