import datetime
import os
from os.path import join
import shlex
import shutil
from subprocess import Popen, check_call, PIPE

from bioluigi.tasks import sratoolkit
import luigi
from luigi.util import requires
import pandas as pd

from ..config import rnaseq_pipeline
from ..utils import DynamicWrapperTask

cfg = rnaseq_pipeline()

"""
This module contains all the logic to retrieve RNA-Seq data from SRA.
"""

class PrefetchSraFastq(luigi.Task):
    """
    Prefetch a SRR sample using prefetch

    Data is downloaded in a shared SRA cache.

    :attr srr: A SRA run accession
    """
    srr = luigi.Parameter()

    def run(self):
        yield sratoolkit.Prefetch(self.srr,
                                  self.output().path,
                                  max_size=40,
                                  extra_args=shlex.split(cfg.PREFETCH_ARGS),
                                  scheduler_extra_args=['--partition', 'Wormhole'])

    def output(self):
        return luigi.LocalTarget(join(cfg.SRA_PUBLIC_DIR, '{}.sra'.format(self.srr)))

@requires(PrefetchSraFastq)
class DumpSraFastq(luigi.Task):
    """
    Dump FASTQs from a SRR archive

    FASTQs are organized by :gsm: in a flattened layout.

    :attr srr: SRA experiment accession used as a parent folder for the run
    """
    srx = luigi.Parameter()

    paired_reads = luigi.BoolParameter(positional=False)

    def run(self):
        yield sratoolkit.FastqDump(self.input().path,
                                   os.path.dirname(self.output()[0].path),
                                   paired_reads=self.paired_reads)

    def output(self):
        output_dir = join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx)
        if self.paired_reads:
            return [luigi.LocalTarget(join(output_dir, self.srr + '_1.fastq.gz')),
                    luigi.LocalTarget(join(output_dir, self.srr + '_2.fastq.gz'))]
        return [luigi.LocalTarget(join(output_dir, self.srr + '_1.fastq.gz'))]

class DownloadSraExperimentRunInfo(luigi.Task):
    srx = luigi.Parameter()

    resources = {'edirect_http_connections': 1}

    def run(self):
        with self.output().open('w') as f:
            esearch_proc = Popen(['esearch', '-db', 'sra', '-query', self.srx], stdout=PIPE)
            check_call(['efetch', '-format', 'runinfo'], stdin=esearch_proc.stdout, stdout=f)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'sra', '{}.runinfo'.format(self.srx)))

@requires(DownloadSraExperimentRunInfo)
class DownloadSraExperiment(DynamicWrapperTask):

    @property
    def sample_id(self):
        return self.srx

    def run(self):
        # this will raise an error of no FASTQs are related
        df = pd.read_csv(self.input().path)

        latest_run = df.sort_values('Run', ascending=False).iloc[0]

        is_paired = latest_run.LibraryLayout == 'PAIRED'

        yield DumpSraFastq(latest_run.Run, self.srx, paired_reads=is_paired)

class DownloadSraProjectRunInfo(luigi.Task):
    srp = luigi.Parameter()

    resources = {'edirect_http_connections': 1}

    def run(self):
        with self.output().open('w') as f:
            esearch_proc = Popen(['esearch', '-db', 'sra', '-query', self.srp], stdout=PIPE)
            check_call(['efetch', '-format', 'runinfo'], stdin=esearch_proc.stdout, stdout=f)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'sra', '{}.runinfo'.format(self.srp)))

@requires(DownloadSraProjectRunInfo)
class DownloadSraProject(DynamicWrapperTask):
    def run(self):
        df = pd.read_csv(self.input().path)
        # TODO: test this code
        yield [DownloadSraExperiment(experiment) for experiment, runs in df.groupby('Experiment')]
