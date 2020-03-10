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

class PrefetchSraRun(luigi.Task):
    """
    Prefetch a SRA run using prefetch from sratoolkit

    SRA archives are stored in a shared cache.
    """
    srr = luigi.Parameter(description='SRA run identifier')

    def run(self):
        yield sratoolkit.Prefetch(self.srr,
                                  self.output().path,
                                  max_size=40,
                                  extra_args=shlex.split(cfg.PREFETCH_ARGS),
                                  scheduler_extra_args=['--partition', 'Wormhole'])

    def output(self):
        return luigi.LocalTarget(join(cfg.SRA_PUBLIC_DIR, '{}.sra'.format(self.srr)))

@requires(PrefetchSraRun)
class DumpSraRun(luigi.Task):
    """
    Dump FASTQs from a SRA run archive
    """
    srx = luigi.Parameter(description='SRA experiment identifier')

    paired_reads = luigi.BoolParameter(positional=False, description='Indicate of reads have paired or single mates')

    def run(self):
        yield sratoolkit.FastqDump(self.input().path,
                                   join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx),
                                   paired_reads=self.paired_reads,
                                   minimum_read_length=25)

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
    """
    Download a SRA experiment comprising one SRA run

    It is possible for experiments to be reprocessed in SRA leading to multiple
    associated runs. The default is to select the latest run based on the
    lexicographic order of its identifier.
    """
    srr = luigi.OptionalParameter(default=None, description='Specific SRA run accession to use (defaults to latest)')

    @property
    def sample_id(self):
        return self.srx

    def run(self):
        # this will raise an error of no FASTQs are related
        df = pd.read_csv(self.input().path)

        if self.srr is not None:
            run = df[df.Run == self.srr].iloc[0]
        else:
            run = df.sort_values('Run', ascending=False).iloc[0]

        is_paired = run.LibraryLayout == 'PAIRED'

        yield DumpSraRun(run.Run, self.srx, paired_reads=is_paired)

class DownloadSraProjectRunInfo(luigi.Task):
    """
    Download a SRA project
    """
    srp = luigi.Parameter(description='SRA project identifier')

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
        yield [DownloadSraExperiment(experiment) for experiment, runs in df.groupby('Experiment')]

@requires(DownloadSraProjectRunInfo, DownloadSraProject)
class ExtractSraProjectBatchInfo(luigi.Task):
    """
    Extract the batch information for a given SRA project.
    """

    def run(self):
        run_info, samples = self.input()
        with self.output().open('w') as info_out:
            for (experiment_id, row), fastqs in zip(run_info.groupby('Experiment').first().items(), samples):
                for fastq in fastqs:
                    # strip the two extensions (.fastq.gz)
                    fastq_name, _ = os.path.splitext(fastq.path)
                    fastq_name, _ = os.path.splitext(fastq_name)
                    fastq_id = os.path.basename(fastq_name)
                    srx_uri = 'https://www.ncbi.nlm.nih.gov/sra?term={}'.format(row.Experiment)
                    with gzip.open(fastq.path, 'rt') as f:
                        fastq_header = f.readline().rstrip()
                    info_out.write('\t'.join([experiment_id, fastq_id, row.Platform, srx_uri, fastq_header]) + '\n')

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.BATCHINFODIR, 'sra', '{}.fastq-headers-table'.format(self.srp)))
