import gzip
import logging
import os
from os.path import join
import shlex
import subprocess
from subprocess import Popen, check_call, PIPE
import xml.etree.ElementTree as ET

from bioluigi.tasks import sratoolkit
from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask
import luigi
from luigi.util import requires
import pandas as pd

from ..config import rnaseq_pipeline
from ..utils import remove_task_output

class sra(luigi.Config):
    task_namespace = 'rnaseq_pipeline.sources'

    paired_read_experiments = luigi.ListParameter(description='List of SRA experiments known to contain paired reads')

cfg = rnaseq_pipeline()
sra_cfg = sra()

logger = logging.getLogger('luigi-interface')

"""
This module contains all the logic to retrieve RNA-Seq data from SRA.
"""

class PrefetchSraRun(luigi.Task):
    """
    Prefetch a SRA run using prefetch from sratoolkit

    SRA archives are stored in a shared cache.
    """
    srr = luigi.Parameter(description='SRA run identifier')

    @staticmethod
    def _get_ncbi_public_dir():
        ret = subprocess.run(['vdb-config', '-p'], stdout=subprocess.PIPE, universal_newlines=True)
        config_xml = ET.fromstring(ret.stdout)
        return config_xml.find('repository').find('user').find('main').find('public').find('root').text

    def run(self):
        yield sratoolkit.Prefetch(self.srr,
                                  self.output().path,
                                  max_size=65,
                                  scheduler_partition='Wormhole')

    def output(self):
        return luigi.LocalTarget(join(self._get_ncbi_public_dir(), 'sra', f'{self.srr}.sra'))

@requires(PrefetchSraRun)
class DumpSraRun(luigi.Task):
    """
    Dump FASTQs from a SRA run archive
    """
    srx = luigi.Parameter(description='SRA experiment identifier')

    paired_reads = luigi.BoolParameter(positional=False, description='Indicate of reads have paired or single mates')

    def on_success(self):
        # cleanup SRA archive once dumped if it's still hanging around
        dump_sra_run_task = self.requires()
        remove_task_output(dump_sra_run_task)
        return super().on_success()

    def run(self):
        yield sratoolkit.FastqDump(self.input().path,
                                   join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx))
        if not self.complete():
            raise RuntimeError(f'{repr(self)} was not completed after successful run.')

    def output(self):
        output_dir = join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx)
        if self.paired_reads:
            return [luigi.LocalTarget(join(output_dir, self.srr + '_1.fastq.gz')),
                    luigi.LocalTarget(join(output_dir, self.srr + '_2.fastq.gz'))]
        return [luigi.LocalTarget(join(output_dir, self.srr + '.fastq.gz'))]

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
class DownloadSraExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
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

    @property
    def platform(self):
        return IlluminaPlatform('HiSeq 2500')

    def run(self):
        # this will raise an error of no FASTQs are related
        df = pd.read_csv(self.input().path)

        if self.srr is not None:
            run = df[df.Run == self.srr].iloc[0]
        else:
            run = df.sort_values('Run', ascending=False).iloc[0]

        # layout is very often not annotated correctly and it is best to rely
        # on the number of mates per spot
        is_paired = (self.sample_id in sra_cfg.paired_read_experiments) or (run.spots_with_mates > 0)

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
class DownloadSraProject(DynamicTaskWithOutputMixin, DynamicWrapperTask):
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
