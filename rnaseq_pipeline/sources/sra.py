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

# TODO: decouple this from GEO-related code

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

    :attr gsm: Geo Sample identifier
    """
    gsm = luigi.Parameter()

    paired_reads = luigi.BoolParameter(positional=False)

    def run(self):
        yield sratoolkit.FastqDump(self.input().path,
                                   os.path.dirname(self.output()[0].path),
                                   paired_reads=self.paired_reads)

    def output(self):
        output_dir = join(cfg.OUTPUT_DIR, cfg.DATA, 'geo', self.gsm)
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
    def run(self):
        # this will raise an error of no FASTQs are related
        df = pd.read_csv(self.input().path)

        latest_run = df.sort_values('Run', ascending=False).iloc[0]

        yield DumpSraFastq(latest_run.Run, self.srx, paired_reads=latest_run.LibraryLayout == 'PAIRED')

class DownloadSraProject(DynamicWrapperTask):
    srp = luigi.Parameter()
    def run(self):
        yield []
