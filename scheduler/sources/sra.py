import datetime
import os
from os.path import join
import shlex
from subprocess import Popen, check_call, PIPE

from bioluigi.tasks import sratoolkit
import luigi
from luigi.util import requires

from ..config import rnaseq_pipeline

cfg = rnaseq_pipeline()

"""
This module contains all the logic to retrieve RNA-Seq data from SRA.
"""

# TODO: decouple this from GEO-related code

class PrefetchSraFastq(luigi.Task):
    """
    Prefetch a SRR sample using prefetch

    Data is downloaded in a shared SRA cache.
    """
    srr = luigi.Parameter()

    resources = {'sra_connections': 1}

    def run(self):
        yield sratoolkit.Prefetch(self.srr,
                                  self.output().path,
                                  max_size=30,
                                  extra_args=shlex.split(cfg.PREFETCH_ARGS))

    def output(self):
        return luigi.LocalTarget(join(cfg.SRA_PUBLIC_DIR, '{}.sra'.format(self.srr)))

@requires(PrefetchSraFastq)
class DumpSraFastq(luigi.Task):
    """
    Dump FASTQs from a SRR archive

    FASTQs are organized by :gsm: in a flattened layout.

    :param gsm: Geo Sample identifier
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
        return [luigi.LocalTarget(join(output_dir, self.gsm, self.srr + '_1.fastq.gz'))]
