import gzip
import logging
import os
import subprocess
import xml.etree.ElementTree as ET
from datetime import timedelta
from os.path import join
from subprocess import Popen, check_output, PIPE

import luigi
import pandas as pd
from bioluigi.tasks import sratoolkit
from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask, TaskWithMetadataMixin
from luigi.util import requires

from ..config import rnaseq_pipeline
from ..platforms import IlluminaPlatform
from ..targets import ExpirableLocalTarget
from ..utils import remove_task_output, RerunnableTaskMixin

cfg = rnaseq_pipeline()

logger = logging.getLogger('luigi-interface')

def read_runinfo(path):
    SRA_RUNINFO_COLUMNS = 'Run,ReleaseDate,LoadDate,spots,bases,spots_with_mates,avgLength,size_MB,AssemblyName,download_path,Experiment,LibraryName,LibraryStrategy,LibrarySelection,LibrarySource,LibraryLayout,InsertSize,InsertDev,Platform,Model,SRAStudy,BioProject,Study_Pubmed_id,ProjectID,Sample,BioSample,SampleType,TaxID,ScientificName,SampleName,g1k_pop_code,source,g1k_analysis_group,Subject_ID,Sex,Disease,Tumor,Affection_Status,Analyte_Type,Histological_Type,Body_Site,CenterName,Submission,dbgap_study_accession,Consent,RunHash,ReadHash'.split(
        ',')
    df = pd.read_csv(path)
    if df.columns[0] != 'Run':
        logger.warning('Runinfo file %s is missing a header, a fallback will be used instead.', path)
        # re-read with a list of known columns as a fallback
        df = pd.read_csv(path, names=SRA_RUNINFO_COLUMNS[:len(df.columns)])
    return df

"""
This module contains all the logic to retrieve RNA-Seq data from SRA.
"""

class PrefetchSraRun(TaskWithMetadataMixin, luigi.Task):
    """
    Prefetch a SRA run using prefetch from sratoolkit

    SRA archives are stored in a shared cache.
    """
    srr = luigi.Parameter(description='SRA run identifier')

    retry_count = 3

    @staticmethod
    def _get_ncbi_public_dir():
        ret = subprocess.run(['vdb-config', '-p'], stdout=subprocess.PIPE, universal_newlines=True)
        config_xml = ET.fromstring(ret.stdout)
        return config_xml.find('repository').find('user').find('main').find('public').find('root').text

    def run(self):
        yield sratoolkit.Prefetch(self.srr,
                                  self.output().path,
                                  max_size=100,
                                  scheduler_partition='Wormhole',
                                  metadata=self.metadata,
                                  walltime=timedelta(hours=2))

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
                                   join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx),
                                   metadata=self.metadata)
        if not self.complete():
            labelling = 'paired' if self.paired_reads else 'single-end'
            raise RuntimeError(
                f'{repr(self)} was not completed after successful fastq-dump execution. Is it possible the SRA run is mislabelled as {labelling}?')

    def output(self):
        output_dir = join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx)
        if self.paired_reads:
            return [luigi.LocalTarget(join(output_dir, self.srr + '_1.fastq.gz')),
                    luigi.LocalTarget(join(output_dir, self.srr + '_2.fastq.gz'))]
        return [luigi.LocalTarget(join(output_dir, self.srr + '.fastq.gz'))]

class EmptyRunInfoError(Exception):
    pass

def retrieve_runinfo(sra_accession):
    """Retrieve a SRA runinfo using search and efetch utilities"""
    esearch_proc = Popen(['esearch', '-db', 'sra', '-query', sra_accession], stdout=PIPE)
    runinfo_data = check_output(['efetch', '-format', 'runinfo'], universal_newlines=True, stdin=esearch_proc.stdout)
    if not runinfo_data.strip() or (len(runinfo_data.splitlines()) == 1 and runinfo_data[:3] == 'Run'):
        raise EmptyRunInfoError(f"Runinfo for {sra_accession} is empty.")
    return runinfo_data

class DownloadSraExperimentRunInfo(TaskWithMetadataMixin, RerunnableTaskMixin, luigi.Task):
    srx = luigi.Parameter(description='SRX accession to use')

    resources = {'edirect_http_connections': 1}

    # retry this task at least once (see https://github.com/PavlidisLab/rnaseq-pipeline/issues/66)
    retry_count = 1

    def run(self):
        if self.output().is_stale():
            logger.info('%s is stale, redownloading...', self.output())
        with self.output().open('w') as f:
            f.write(retrieve_runinfo(self.srx))

    def output(self):
        return ExpirableLocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'sra', '{}.runinfo'.format(self.srx)),
                                    ttl=timedelta(days=14))

@requires(DownloadSraExperimentRunInfo)
class DownloadSraExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Download a SRA experiment comprising one SRA run

    It is possible for experiments to be reprocessed in SRA leading to multiple
    associated runs. The default is to select the latest run based on the
    lexicographic order of its identifier.
    """
    srr = luigi.OptionalParameter(default=None, description='Specific SRA run accession to use (defaults to latest)')

    force_single_end = luigi.BoolParameter(positional=False, significant=False, default=False,
                                           description='Force the library layout to be single-end')
    force_paired_reads = luigi.BoolParameter(positional=False, significant=False, default=False,
                                             description='Force the library layout to be paired')

    @property
    def sample_id(self):
        return self.srx

    @property
    def platform(self):
        return IlluminaPlatform('HiSeq 2500')

    def run(self):
        # this will raise an error of no FASTQs are related
        df = read_runinfo(self.input().path)

        if self.srr is not None:
            run = df[df.Run == self.srr].iloc[0]
        else:
            run = df.sort_values('Run', ascending=False).iloc[0]

        if self.force_paired_reads:
            is_paired = True
        elif self.force_single_end:
            is_paired = False
        else:
            is_paired = run.LibraryLayout == 'PAIRED'

        metadata = dict(self.metadata)
        # do not override the sample_id when invoked from DownloadGeoSample or DownloadGemmaExperiment
        if 'sample_id' not in metadata:
            metadata['sample_id'] = self.sample_id
        yield DumpSraRun(run.Run, self.srx, paired_reads=is_paired, metadata=metadata)

class DownloadSraProjectRunInfo(TaskWithMetadataMixin, RerunnableTaskMixin, luigi.Task):
    """
    Download a SRA project
    """
    srp = luigi.Parameter(description='SRA project identifier')

    resources = {'edirect_http_connections': 1}

    # retry this task at least once (see https://github.com/PavlidisLab/rnaseq-pipeline/issues/66)
    retry_count = 1

    def run(self):
        with self.output().open('w') as f:
            f.write(retrieve_runinfo(self.srp))

    def output(self):
        return ExpirableLocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'sra', '{}.runinfo'.format(self.srp)),
                                    ttl=timedelta(days=14))

@requires(DownloadSraProjectRunInfo)
class DownloadSraProject(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    ignored_samples = luigi.ListParameter(default=[], description='Ignored SRX identifiers')

    def run(self):
        df = read_runinfo(self.input().path)
        yield [DownloadSraExperiment(experiment, metadata=self.metadata) for experiment, runs in
               df.groupby('Experiment') if experiment not in self.ignored_samples]

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
        return luigi.LocalTarget(
            join(cfg.OUTPUT_DIR, cfg.BATCHINFODIR, 'sra', '{}.fastq-headers-table'.format(self.srp)))
