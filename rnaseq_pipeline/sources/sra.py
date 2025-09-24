"""
This module contains all the logic to retrieve RNA-Seq data from SRA.
"""
import enum
import gzip
import logging
import os
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import timedelta
from os.path import join
from typing import Optional, List

import luigi
import pandas as pd
from bioluigi.tasks import sratoolkit
from bioluigi.tasks.utils import TaskWithMetadataMixin, DynamicTaskWithOutputMixin, DynamicWrapperTask
from luigi.util import requires

from ..config import rnaseq_pipeline
from ..platforms import IlluminaPlatform
from ..rnaseq_utils import SequencingFileType, detect_layout
from ..targets import ExpirableLocalTarget, DownloadRunTarget
from ..utils import remove_task_output, RerunnableTaskMixin

cfg = rnaseq_pipeline()

logger = logging.getLogger(__name__)

class sra(luigi.Config):
    task_namespace = 'rnaseq_pipeline.sources'
    ncbi_public_dir: str = luigi.Parameter()

sra_config = sra()

# columns to use when a runinfo file lacks a header
SRA_RUNINFO_COLUMNS = ['Run', 'ReleaseDate', 'LoadDate', 'spots', 'bases', 'spots_with_mates', 'avgLength', 'size_MB',
                       'AssemblyName', 'download_path', 'Experiment', 'LibraryName', 'LibraryStrategy',
                       'LibrarySelection', 'LibrarySource', 'LibraryLayout', 'InsertSize', 'InsertDev', 'Platform',
                       'Model', 'SRAStudy', 'BioProject', 'Study_Pubmed_id', 'ProjectID', 'Sample', 'BioSample',
                       'SampleType', 'TaxID', 'ScientificName', 'SampleName', 'g1k_pop_code', 'source',
                       'g1k_analysis_group', 'Subject_ID', 'Sex', 'Disease', 'Tumor', 'Affection_Status',
                       'Analyte_Type', 'Histological_Type', 'Body_Site', 'CenterName', 'Submission',
                       'dbgap_study_accession', 'Consent', 'RunHash', 'ReadHash']

def read_runinfo(path):
    df = pd.read_csv(path)
    if df.columns[0] != 'Run':
        logger.warning('Runinfo file %s is missing a header, a fallback will be used instead.', path)
        # re-read with a list of known columns as a fallback
        df = pd.read_csv(path, names=SRA_RUNINFO_COLUMNS[:len(df.columns)])
    return df

class SraRunIssue(enum.IntFlag):
    """Issues that can occur when processing SRA runs."""
    NO_SRA_FILES = enum.auto()
    NO_SPOT_STATISTICS = enum.auto()
    NO_FASTQ_LOAD = enum.auto()
    NO_FASTQ_LOAD_OPTIONS = enum.auto()
    MISMATCHED_FASTQ_LOAD_OPTIONS = enum.auto()
    AMBIGUOUS_READ_SIZES = enum.auto()
    MISMATCHED_READ_SIZES = enum.auto()
    INVALID_RUN = enum.auto()

class SraReadType(enum.Enum):
    """
    Type of read in a spot.
    """
    TECHNICAL = 'T'
    BIOLOGICAL = 'B'

@dataclass
class SraRunMetadata:
    """A digested SRA run metadata"""
    srx: str
    srr: str
    is_single_end: bool
    is_paired: bool
    fastq_filenames: Optional[list[str]]
    fastq_file_sizes: Optional[list[int]]
    # currently only available if --readTypes options were passed to the fastq-load.py loader, I'd like to know if this
    # is stored elsewhere though, because I can see it in the UI.
    read_types: Optional[list[SraReadType]]
    # only available if statistics were present in the XML metadata
    number_of_spots: Optional[int]
    average_read_lengths: Optional[list[float]]
    fastq_load_options: Optional[dict]
    layout: list[SequencingFileType]
    issues: SraRunIssue

def read_xml_metadata(path, include_invalid_runs=False) -> List[SraRunMetadata]:
    """
    Extract transcriptomic RNA-Seq runs from the given SRA XML metadata file.
    :param path: Path to the XML file containing SRA run metadata.
    :param include_invalid_runs: If True, include runs that do not have any suitable metadata that can be used to
    determine the layout.
    :return:
    """
    root = ET.parse(path)
    runs = root.findall('EXPERIMENT_PACKAGE/RUN_SET/RUN')
    result = []
    for run in runs:
        srr = run.attrib['accession']

        srx = run.find('EXPERIMENT_REF').attrib['accession']

        library_strategy = root.find(
            'EXPERIMENT_PACKAGE/EXPERIMENT[@accession=\'' + srx + '\']/DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_STRATEGY')
        library_source = root.find(
            'EXPERIMENT_PACKAGE/EXPERIMENT[@accession=\'' + srx + '\']/DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_SOURCE')

        if library_strategy is not None and library_strategy.text not in ['RNA-Seq']:
            logger.warning('%s Ignoring run with %s library strategy.', srr, library_strategy.text)
            continue

        if library_source is not None and library_source.text not in ['TRANSCRIPTOMIC', 'TRANSCRIPTOMIC SINGLE CELL']:
            logger.warning('%s: Ignoring run with %s library source.', srr, library_source.text)
            continue

        is_single_end = root.find(
            'EXPERIMENT_PACKAGE/EXPERIMENT[@accession=\'' + srx + '\']/DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_LAYOUT/SINGLE') is not None
        is_paired = root.find(
            'EXPERIMENT_PACKAGE/EXPERIMENT[@accession=\'' + srx + '\']/DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_LAYOUT/PAIRED') is not None

        sra_files = run.findall('SRAFiles/SRAFile[@semantic_name=\'fastq\']')

        issues = SraRunIssue(0)

        if not sra_files:
            issues |= SraRunIssue.NO_SRA_FILES

        # if the data was loaded with fastq-load.py, we can obtain the order of the files from the options
        loader, options = None, None
        run_attributes = run.findall('RUN_ATTRIBUTES/RUN_ATTRIBUTE')
        for run_attribute in run_attributes:
            tag, value = run_attribute.find('TAG'), run_attribute.find('VALUE')
            if tag.text == 'loader':
                loader = value.text
            elif tag.text == 'options':
                options = value.text
                options = {k: v for k, v in
                           (o.split('=', maxsplit=1) if '=' in o else (o, None) for o in options.split())}

        if loader == 'fastq-load.py':
            # parse options...
            # TODO: use argparse or something safer
            fastq_load_read_types = None
            fastq_load_files = []
            if options:
                if '--readTypes' in options and options['--readTypes'] is not None:
                    fastq_load_read_types = [SraReadType.BIOLOGICAL if rt == 'B' else SraReadType.TECHNICAL for rt in
                                             str(options['--readTypes'])]
                opts = ['--read1PairFiles',
                        '--read2PairFiles',
                        '--read3PairFiles',
                        '--read4PairFiles']
                for o in opts:
                    if o in options:
                        fastq_load_files.append(options[o])
            else:
                logger.warning('%s: The fastq-load.py loader does not have any option.', srr)
                fastq_load_files = None
                issues |= SraRunIssue.NO_FASTQ_LOAD_OPTIONS
        else:
            issues |= SraRunIssue.NO_FASTQ_LOAD
            fastq_load_read_types = None
            fastq_load_files = None

        statistics = run.find('Statistics')
        if statistics is not None:
            number_of_spots = int(statistics.attrib['nreads'])
            reads = sorted(statistics.findall('Read'), key=lambda r: int(r.attrib['index']))
            spot_read_lengths = [float(r.attrib['average']) for r in reads]
        else:
            logger.warning(
                '%s: No spot statistics found, cannot use the average read lengths to determine the order of the FASTQ files.',
                srr)
            number_of_spots = None
            reads = None
            spot_read_lengths = None
            issues |= SraRunIssue.NO_SPOT_STATISTICS

        # sort the SRA files to match the spots using fastq-load.py options
        if loader == 'fastq-load.py' and fastq_load_files:

            if set(fastq_load_files) == set([sf.attrib['filename'] for sf in sra_files]):
                logger.info('%s: Using the arguments passed to fastq-load.py to reorder the SRA files.', srr)
                sra_files = sorted(sra_files, key=lambda f: fastq_load_files.index(f.attrib['filename']))
                fastq_filenames = [sf.attrib['filename'] for sf in sra_files]
                fastq_file_sizes = [int(sf.attrib['size']) for sf in sra_files]
                read_types = fastq_load_read_types

            # try to add a .gz suffix to the SRA files
            elif set(fastq_load_files) == set([sf.attrib['filename'] + '.gz' for sf in sra_files]):
                logger.warning(
                    '%s: The SRA files lack .gz extensions: %s, but still correspond to fastq-load.py options: %s, will use those to reorder the SRA files.',
                    srx, ', '.join(sf.attrib['filename'] for sf in sra_files), ', '.join(fastq_load_files))
                sra_files = sorted(sra_files,
                                   key=lambda f: fastq_load_files.index(f.attrib['filename'] + '.gz'))
                fastq_filenames = [sf.attrib['filename'] for sf in sra_files]
                fastq_file_sizes = [int(sf.attrib['size']) for sf in sra_files]
                read_types = fastq_load_read_types

            elif sra_files:
                logging.warning(
                    "%s: The SRA files: %s do not match arguments passed to fastq-load.py: %s. The filenames passed to fastq-load.py will be used instead: %s.",
                    srr,
                    ', '.join(sf.attrib['filename'] for sf in sra_files),
                    ' '.join(k + '=' + v if v else 'k' for k, v in options.items()),
                    fastq_load_files)
                fastq_filenames = fastq_load_files
                fastq_file_sizes = None
                read_types = fastq_load_read_types
                issues |= SraRunIssue.MISMATCHED_FASTQ_LOAD_OPTIONS

            else:
                logging.warning(
                    "%s: No SRA files found, but the arguments of fastq-load.py are present: %s. The filenames passed to fastq-load.py will be used: %s.",
                    srr, ' '.join(k + '=' + v if v else 'k' for k, v in options.items()), ', '.join(fastq_load_files))
                fastq_filenames = fastq_load_files
                fastq_file_sizes = None
                read_types = fastq_load_read_types

        # use spot statistics to determine the order of the files by matching their sizes with the sizes of the files
        # this is less reliable than using the fastq-load.py options, but it is still better than nothing
        # we can only use this strategy if all the read sizes are different and can be related to the file sizes
        elif statistics is not None:
            # check if the sizes are unambiguous?
            read_sizes = [int(read.attrib['count']) * float(read.attrib['average']) for read in reads]
            if len(set(read_sizes)) == len(read_sizes):
                if sra_files:
                    # sort the files according to the layout
                    # sort the layout according to the average read size
                    reads_by_size = [e[0] for e in sorted(enumerate(reads),
                                                          key=lambda e: int(e[1].attrib['count']) * float(
                                                              e[1].attrib['average']))]
                    files_by_size = [e[0] for e in sorted(enumerate(sra_files), key=lambda e: int(e[1].attrib['size']))]

                    if len(reads_by_size) == len(files_by_size):
                        if reads_by_size != files_by_size:
                            logger.info('%s: Reordering SRA files to match the read sizes in the spot...', srr)
                            sra_files = [sra_files[reads_by_size.index(files_by_size[i])] for i, sra_file in
                                         enumerate(sra_files)]
                        fastq_filenames = [sf.attrib['filename'] for sf in sra_files]
                        fastq_file_sizes = [int(sf.attrib['size']) for sf in sra_files]
                        read_types = None
                    else:
                        logger.warning(
                            '%s: The number of reads: %d and files: %d do not correspond, cannot use them to order SRA files by filesize. Only the spot metadata will be used to determine the layout.',
                            srr, len(reads_by_size), len(files_by_size))
                        fastq_filenames = None
                        fastq_file_sizes = None
                        read_types = None
                        issues |= SraRunIssue.MISMATCHED_READ_SIZES
                else:
                    # this is extremely common, so it's not worth warning about it
                    logger.info(
                        '%s: No SRA file to order. Only the spot metadata will be used to determine the layout.',
                        srr)
                    fastq_filenames = None
                    fastq_file_sizes = None
                    read_types = None
                    issues |= SraRunIssue.NO_SRA_FILES
            else:
                # this is extremely common, so it's not worth warning about it
                logger.info(
                    '%s: Number of bps per read are ambiguous: %s, cannot use them to order SRA files by filesize. Only the spot metadata will be used to determine the layout.',
                    srr, read_sizes)
                fastq_filenames = None
                fastq_file_sizes = None
                read_types = None
                issues |= SraRunIssue.AMBIGUOUS_READ_SIZES

        else:
            issues |= SraRunIssue.INVALID_RUN
            logger.info(
                '%s: No information found that can be used to order SRA files, ignoring that run.',
                srr)
            if include_invalid_runs:
                fastq_filenames = [sf.attrib['filename'] for sf in sra_files]
                fastq_file_sizes = [int(sf.attrib['size']) for sf in sra_files]
                result.append(SraRunMetadata(srx, srr,
                                             is_single_end=is_single_end,
                                             is_paired=is_paired,
                                             fastq_filenames=fastq_filenames,
                                             fastq_file_sizes=fastq_file_sizes,
                                             read_types=None,
                                             number_of_spots=None,
                                             average_read_lengths=None,
                                             fastq_load_options=None,
                                             layout=[],
                                             issues=issues))
            continue

        try:
            layout = detect_layout(srr, fastq_filenames, fastq_file_sizes, spot_read_lengths, is_single_end, is_paired)
        except ValueError:
            logger.warning('%s: Failed to detect layout, ignoring that run.', srr, exc_info=True)
            if include_invalid_runs:
                layout = []
                issues |= SraRunIssue.INVALID_RUN
            else:
                continue

        result.append(SraRunMetadata(srx, srr,
                                     is_single_end=is_single_end,
                                     is_paired=is_paired,
                                     fastq_filenames=fastq_filenames,
                                     fastq_file_sizes=fastq_file_sizes,
                                     read_types=read_types,
                                     number_of_spots=number_of_spots,
                                     average_read_lengths=spot_read_lengths,
                                     fastq_load_options=options if loader == 'fastq-load.py' else None,
                                     layout=layout,
                                     issues=issues))
    return result

class PrefetchSraRun(TaskWithMetadataMixin, luigi.Task):
    """
    Prefetch a SRA run using prefetch from sratoolkit

    SRA archives are stored in a shared cache.
    """
    srr: str = luigi.Parameter(description='SRA run identifier')

    retry_count = 3

    def run(self):
        yield sratoolkit.Prefetch(srr_accession=self.srr,
                                  output_file=self.output().path,
                                  max_size=100,
                                  scheduler_partition='Wormhole',
                                  metadata=self.metadata,
                                  walltime=timedelta(hours=2))

    def output(self):
        return luigi.LocalTarget(join(sra_config.ncbi_public_dir, 'sra', f'{self.srr}.sra'))

@requires(PrefetchSraRun)
class DumpSraRun(luigi.Task):
    """
    Dump FASTQs from a SRA run archive
    """
    srx: str = luigi.Parameter(description='SRA experiment identifier')
    srr: str

    layout: list[str] = luigi.ListParameter(positional=False,
                                            description='Indicate the type of each output file from the run. Possible values are I1, I2, R1 and R2.')

    metadata: dict

    def on_success(self):
        # cleanup SRA archive once dumped if it's still hanging around
        dump_sra_run_task = self.requires()
        remove_task_output(dump_sra_run_task)
        return super().on_success()

    def run(self):
        yield sratoolkit.FastqDump(input_file=self.input().path,
                                   output_dir=join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx),
                                   split='files',
                                   number_of_reads_per_spot=len(self.layout),
                                   metadata=self.metadata)
        if not self.complete():
            raise RuntimeError(
                f'{repr(self)} was not completed after successful fastq-dump execution; are the output files respecting the following layout: {self.layout}?')

    def output(self):
        output_dir = join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx)
        expected_files = len(self.layout)
        if expected_files > 1:
            return DownloadRunTarget(self.srr, [join(output_dir, self.srr + '_' + str(i) + '.fastq.gz') for i in
                                      range(1, expected_files + 1)], self.layout)
        return DownloadRunTarget(self.srr, [join(output_dir, self.srr + '.fastq.gz')], self.layout)

class EmptyRunInfoError(Exception):
    pass

def retrieve_sra_metadata(sra_accession, format='runinfo'):
    """Retrieve a SRA runinfo using search and efetch utilities"""
    if isinstance(sra_accession, str):
        p = subprocess.run(['efetch', '-db', 'sra', '-id', sra_accession, '-format', format],
                           text=True, stdout=subprocess.PIPE, check=True)
    else:
        logger.info('Passing ' + str(len(sra_accession)) + ' SRX accessions to efetch...')
        p = subprocess.run(['efetch', '-db', 'sra', '-format', format], input='\n'.join(sra_accession),
                           text=True, stdout=subprocess.PIPE, check=True)
    runinfo_data = p.stdout.strip()
    if format == 'runinfo' and not runinfo_data or (len(runinfo_data.splitlines()) == 1 and runinfo_data[:3] == 'Run'):
        raise EmptyRunInfoError(f"Runinfo for {sra_accession} is empty.")
    return runinfo_data

class DownloadSraExperimentMetadata(TaskWithMetadataMixin, RerunnableTaskMixin, luigi.Task):
    srx = luigi.Parameter(description='SRX accession to use')

    resources = {'edirect_http_connections': 1}

    # retry this task at least once (see https://github.com/PavlidisLab/rnaseq-pipeline/issues/66)
    retry_count = 1

    def run(self):
        if self.output().is_stale():
            logger.info('%s is stale, redownloading...', self.output())
        with self.output().open('w') as f:
            f.write(retrieve_sra_metadata(self.srx, format='xml'))

    def output(self):
        return ExpirableLocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'sra', '{}.xml'.format(self.srx)),
                                    ttl=timedelta(days=14))

@requires(DownloadSraExperimentMetadata)
class DownloadSraExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Download a SRA experiment comprising one SRA run

    It is possible for experiments to be reprocessed in SRA leading to multiple
    associated runs. The default is to select the latest run based on the
    lexicographic order of its identifier.
    """
    srx: str
    srr = luigi.OptionalListParameter(default=None, description='Specific SRA run accessions to use (defaults to all)')

    metadata: dict

    unpack_singleton = False

    @property
    def sample_id(self):
        return self.srx

    @property
    def platform(self):
        return IlluminaPlatform('HiSeq 2500')

    def run(self):
        meta = read_xml_metadata(self.input().path)

        if self.srr is not None:
            meta = [r for r in meta if r.srr in self.srr]

        if not meta:
            raise ValueError(f'No valid SRA runs found for {self.srx}. Valid runs must be transcriptomic RNA-Seq.')

        metadata = dict(self.metadata)
        # do not override the sample_id when invoked from DownloadGeoSample or DownloadGemmaExperiment
        if 'sample_id' not in metadata:
            metadata['sample_id'] = self.sample_id

        for row in meta:
            yield DumpSraRun(srr=row.srr, srx=self.srx, layout=[ft.name for ft in row.layout], metadata=metadata)

class DownloadSraProjectRunInfo(TaskWithMetadataMixin, RerunnableTaskMixin, luigi.Task):
    """
    Download a SRA project
    """
    srp: str = luigi.Parameter(description='SRA project identifier')

    resources = {'edirect_http_connections': 1}

    # retry this task at least once (see https://github.com/PavlidisLab/rnaseq-pipeline/issues/66)
    retry_count = 1

    def run(self):
        with self.output().open('w') as f:
            f.write(retrieve_sra_metadata(self.srp, format='runinfo'))

    def output(self):
        return ExpirableLocalTarget(join(cfg.OUTPUT_DIR, cfg.METADATA, 'sra', '{}.runinfo'.format(self.srp)),
                                    ttl=timedelta(days=14))

@requires(DownloadSraProjectRunInfo)
class DownloadSraProject(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    ignored_samples = luigi.ListParameter(default=[], description='Ignored SRX identifiers')
    metadata: dict

    def run(self):
        df = read_runinfo(self.input().path)
        yield [DownloadSraExperiment(experiment, metadata=self.metadata) for experiment, runs in
               df.groupby('Experiment') if experiment not in self.ignored_samples]

@requires(DownloadSraProjectRunInfo, DownloadSraProject)
class ExtractSraProjectBatchInfo(luigi.Task):
    """
    Extract the batch information for a given SRA project.
    """

    srp: str

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
