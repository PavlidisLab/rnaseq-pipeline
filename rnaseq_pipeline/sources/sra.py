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
from glob import glob
from os.path import join
from typing import Optional, List

import luigi
import pandas as pd
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask
from bioluigi.tasks import sratoolkit, cellranger
from bioluigi.tasks.utils import TaskWithMetadataMixin, DynamicTaskWithOutputMixin, DynamicWrapperTask
from luigi.util import requires

from ..config import Config
from ..platforms import IlluminaPlatform
from ..rnaseq_utils import SequencingFileType, detect_layout
from ..targets import ExpirableLocalTarget, DownloadRunTarget
from ..tenx_utils import read_sequencing_layout_from_10x_bam_header, get_fastq_filenames_for_10x_sequencing_layout, \
    get_fastq_filename
from ..utils import remove_task_output, RerunnableTaskMixin

cfg = Config()

logger = logging.getLogger(__name__)

class SraConfig(luigi.Config):
    @classmethod
    def get_task_family(cls):
        return 'rnaseq_pipeline.sources.sra'

    ncbi_public_dir: str = luigi.Parameter(description='Path to the NCBI public directory.')
    curl_bin: str = luigi.Parameter(default='curl')
    samtools_bin: str = luigi.Parameter(default='samtools')
    bamtofastq_bin: str = luigi.Parameter(default='bamtofastq')
    bam_headers_cache_dir: str = luigi.Parameter(default='bam_headers',
                                                 description='Directory where to store BAM file headers downloaded from SRA files.')

sra_config = SraConfig()

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
    # Indicate if bamtofastq (from Cell Ranger) should be used to extract FASTQs from 10x BAM file(s)
    use_bamtofastq: bool
    # BAM file(s) to extract FASTQs from
    bam_filenames: Optional[list[str]]
    bam_file_urls: Optional[list[str]]
    # Expected FASTQ filenames resulting from bamtofastq on the BAM file(s)
    bam_fastq_filenames: Optional[list[str]]
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

        if library_strategy is not None and library_strategy.text not in ['RNA-Seq', 'ssRNA-seq', 'OTHER']:
            logger.warning('%s Ignoring run with %s library strategy.', srr, library_strategy.text)
            continue

        if library_source is not None and library_source.text not in ['TRANSCRIPTOMIC', 'TRANSCRIPTOMIC SINGLE CELL']:
            logger.warning('%s: Ignoring run with %s library source.', srr, library_source.text)
            continue

        is_single_end = root.find(
            'EXPERIMENT_PACKAGE/EXPERIMENT[@accession=\'' + srx + '\']/DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_LAYOUT/SINGLE') is not None
        is_paired = root.find(
            'EXPERIMENT_PACKAGE/EXPERIMENT[@accession=\'' + srx + '\']/DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_LAYOUT/PAIRED') is not None

        sra_fastq_files = run.findall('SRAFiles/SRAFile[@semantic_name=\'fastq\']')

        sra_10x_bam_files = run.findall('SRAFiles/SRAFile[@semantic_name=\'10X Genomics bam file\']')

        sra_bam_files = run.findall('SRAFiles/SRAFile[@semantic_name=\'bam\']')

        issues = SraRunIssue(0)

        if not sra_fastq_files and not sra_10x_bam_files and not sra_bam_files:
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
                # this is excessively common, so does not warrant a warning
                logger.info('%s: The fastq-load.py loader does not have any option.', srr)
                fastq_load_files = None
                issues |= SraRunIssue.NO_FASTQ_LOAD_OPTIONS
        else:
            issues |= SraRunIssue.NO_FASTQ_LOAD
            fastq_load_read_types = None
            fastq_load_files = None

        statistics = run.find('Statistics')
        if statistics is not None:
            # this may take the value 'variable'
            number_of_spots = int(statistics.attrib['nreads']) if statistics.attrib['nreads'] != 'variable' else None
            reads = sorted(statistics.findall('Read'), key=lambda r: int(r.attrib['index']))
            spot_read_lengths = [float(r.attrib['average']) for r in reads]
            # check for zero-length reads, perform traversal in reverse order to preserve indices
            for i, srl in reversed(list(enumerate(spot_read_lengths))):
                if srl == 0:
                    logger.warning('%s: Empty read for position %d in spot, will ignore it.', srr, i + 1)
                    number_of_spots -= 1
                    reads.pop(i)
                    spot_read_lengths.pop(i)

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

            if set(fastq_load_files) == set([sf.attrib['filename'] for sf in sra_fastq_files]):
                logger.info('%s: Using the arguments passed to fastq-load.py to reorder the SRA files.', srr)
                sra_fastq_files = sorted(sra_fastq_files, key=lambda f: fastq_load_files.index(f.attrib['filename']))
                fastq_filenames = [sf.attrib['filename'] for sf in sra_fastq_files]
                fastq_file_sizes = [int(sf.attrib['size']) for sf in sra_fastq_files]
                use_bamtofastq = False
                bam_filenames = [bf.attrib['filename'] for bf in sra_10x_bam_files]
                bam_file_urls = [bf.attrib['url'] for bf in sra_10x_bam_files]
                bam_fastq_filenames = None
                read_types = fastq_load_read_types

            # try to add a .gz suffix to the SRA files
            elif set(fastq_load_files) == set([sf.attrib['filename'] + '.gz' for sf in sra_fastq_files]):
                logger.warning(
                    '%s: The SRA files lack .gz extensions: %s, but still correspond to fastq-load.py options: %s, will use those to reorder the SRA files.',
                    srx, ', '.join(sf.attrib['filename'] for sf in sra_fastq_files), ', '.join(fastq_load_files))
                sra_fastq_files = sorted(sra_fastq_files,
                                         key=lambda f: fastq_load_files.index(f.attrib['filename'] + '.gz'))
                fastq_filenames = [sf.attrib['filename'] for sf in sra_fastq_files]
                fastq_file_sizes = [int(sf.attrib['size']) for sf in sra_fastq_files]
                use_bamtofastq = False
                bam_filenames = [bf.attrib['filename'] for bf in sra_10x_bam_files]
                bam_file_urls = [bf.attrib['url'] for bf in sra_10x_bam_files]
                bam_fastq_filenames = None
                read_types = fastq_load_read_types

            elif sra_fastq_files:
                logger.warning(
                    "%s: The SRA files: %s do not match arguments passed to fastq-load.py: %s. The filenames passed to fastq-load.py will be used instead: %s.",
                    srr,
                    ', '.join(sf.attrib['filename'] for sf in sra_fastq_files),
                    ' '.join(k + '=' + v if v else 'k' for k, v in options.items()),
                    fastq_load_files)
                fastq_filenames = fastq_load_files
                fastq_file_sizes = None
                use_bamtofastq = False
                bam_filenames = [bf.attrib['filename'] for bf in sra_10x_bam_files]
                bam_file_urls = [bf.attrib['url'] for bf in sra_10x_bam_files]
                bam_fastq_filenames = None
                read_types = fastq_load_read_types
                issues |= SraRunIssue.MISMATCHED_FASTQ_LOAD_OPTIONS

            else:
                logger.warning(
                    "%s: No SRA files found, but the arguments of fastq-load.py are present: %s. The filenames passed to fastq-load.py will be used: %s.",
                    srr, ' '.join(k + '=' + v if v else 'k' for k, v in options.items()), ', '.join(fastq_load_files))
                fastq_filenames = fastq_load_files
                fastq_file_sizes = None
                use_bamtofastq = False
                bam_filenames = [bf.attrib['filename'] for bf in sra_10x_bam_files]
                bam_file_urls = [bf.attrib['url'] for bf in sra_10x_bam_files]
                bam_fastq_filenames = None
                read_types = fastq_load_read_types

        # check for 10x BAM files
        elif sra_10x_bam_files:
            logger.info('%s: Using 10x Genomics BAM files do determine read layout.', srr)
            # we have to read the file(s), unfortunately

            if len(sra_10x_bam_files) > 1:
                # TODO: support multiple BAM files, they must share the same read layout
                logger.warning('%s: Multiple 10x BAM files found, will only use the first one.', srr)
            bam_file = sra_10x_bam_files[0]

            # cache the header of the BAM file
            bam_header_file = read_bam_header(srr, bam_file.attrib['filename'], bam_file.attrib['url'])

            # BAM may contain multiple flowcells and lanes for a given sample
            with open(bam_header_file, 'r') as f:
                flowcells = read_sequencing_layout_from_10x_bam_header(f)
                bam_read_types = None
                for flowcell in flowcells.values():
                    for rt in flowcell.values():
                        if bam_read_types is None:
                            bam_read_types = rt
                        elif bam_read_types != rt:
                            raise NotImplementedError(
                                'Mixture of sequencing layouts in a single 10x BAM file are not supported.')

            if flowcells:
                logger.info('%s: Detected read types from BAM file %s: %s', srr, bam_file.attrib['filename'],
                            ', '.join(rt.name for rt in bam_read_types))
                # FIXME: report FASTQ filenames for all flowcells and lanes
                flowcell = next(iter(flowcells.values()))
                lane_id, read_types = next(iter(flowcell.items()))
                fastq_filenames = [f'bamtofastq_S1_L{lane_id:03}_{rt.name}_001.fastq.gz'
                                   for rt in read_types]

                fastq_file_sizes = None
                read_types = bam_read_types
                # pairedness information is misleading for BAM files
                spot_read_lengths = None
                is_single_end = False
                is_paired = False
                use_bamtofastq = True
                bam_filenames = [bam_file.attrib['filename']]
                bam_file_urls = [bam_file.attrib['url']]
                bam_fastq_filenames = get_fastq_filenames_for_10x_sequencing_layout(flowcells)
            else:
                logger.warning('%s: Failed to detect read types from BAM file, ignoring that run.', srr)
                issues |= SraRunIssue.INVALID_RUN
                if include_invalid_runs:
                    result.append(SraRunMetadata(srx, srr,
                                                 is_single_end=is_single_end,
                                                 is_paired=is_paired,
                                                 fastq_filenames=None,
                                                 fastq_file_sizes=None,
                                                 read_types=None,
                                                 number_of_spots=None,
                                                 average_read_lengths=None,
                                                 fastq_load_options=None,
                                                 use_bamtofastq=False,
                                                 bam_filenames=None,
                                                 bam_file_urls=None,
                                                 bam_fastq_filenames=None,
                                                 layout=[],
                                                 issues=issues))
                continue

        # check for regular BAM files
        elif sra_bam_files:
            logger.info('%s: Using regular BAM files to detect read layout.', srr)

            if len(sra_bam_files) > 1:
                logger.warning('%s: Multiple BAM files found, will only use the first one.', srr)
            bam_file = sra_bam_files[0]

            if is_single_end:
                fastq_filenames = ['R1.fastq.gz']
                fastq_file_sizes = None
                read_types = [SraReadType.BIOLOGICAL]
                use_bamtofastq = True
                bam_filenames = [bam_file.attrib['filename']]
                bam_file_urls = [bam_file.attrib['url']]
                bam_fastq_filenames = ['R1.fastq.gz']
            elif is_paired:
                fastq_filenames = ['R1.fastq.gz', 'R2.fastq.gz']
                fastq_file_sizes = None
                read_types = [SraReadType.BIOLOGICAL, SraReadType.BIOLOGICAL]
                use_bamtofastq = True
                bam_filenames = [bam_file.attrib['filename']]
                bam_file_urls = [bam_file.attrib['url']]
                bam_fastq_filenames = ['R1.fastq.gz', 'R2.fastq.gz']
            else:
                logger.warning('%s: Failed to detect read types from BAM file, ignoring that run.', srr)
                issues |= SraRunIssue.INVALID_RUN
                if include_invalid_runs:
                    result.append(SraRunMetadata(srx, srr,
                                                 is_single_end=is_single_end,
                                                 is_paired=is_paired,
                                                 fastq_filenames=None,
                                                 fastq_file_sizes=None,
                                                 read_types=None,
                                                 number_of_spots=None,
                                                 average_read_lengths=None,
                                                 fastq_load_options=None,
                                                 use_bamtofastq=False,
                                                 bam_filenames=None,
                                                 bam_file_urls=None,
                                                 bam_fastq_filenames=None,
                                                 layout=[],
                                                 issues=issues))
                continue

        # use spot statistics to determine the order of the files by matching their sizes with the sizes of the files
        # this is less reliable than using the fastq-load.py options, but it is still better than nothing
        # we can only use this strategy if all the read sizes are different and can be related to the file sizes
        elif statistics is not None:
            # check if the sizes are unambiguous?
            read_sizes = [int(read.attrib['count']) * float(read.attrib['average']) for read in reads]
            if len(set(read_sizes)) == len(read_sizes):
                if sra_fastq_files:
                    # sort the files according to the layout
                    # sort the layout according to the average read size
                    reads_by_size = [e[0] for e in sorted(enumerate(reads),
                                                          key=lambda e: int(e[1].attrib['count']) * float(
                                                              e[1].attrib['average']))]
                    files_by_size = [e[0] for e in
                                     sorted(enumerate(sra_fastq_files), key=lambda e: int(e[1].attrib['size']))]

                    if len(reads_by_size) == len(files_by_size):
                        if reads_by_size != files_by_size:
                            logger.info('%s: Reordering SRA files to match the read sizes in the spot...', srr)
                            sra_fastq_files = [sra_fastq_files[reads_by_size.index(files_by_size[i])] for i, sra_file in
                                               enumerate(sra_fastq_files)]
                        fastq_filenames = [sf.attrib['filename'] for sf in sra_fastq_files]
                        fastq_file_sizes = [int(sf.attrib['size']) for sf in sra_fastq_files]
                        use_bamtofastq = False
                        bam_filenames = [bf.attrib['filename'] for bf in sra_10x_bam_files]
                        bam_file_urls = [bf.attrib['url'] for bf in sra_10x_bam_files]
                        bam_fastq_filenames = None
                        read_types = None
                    else:
                        logger.warning(
                            '%s: The number of reads: %d and files: %d do not correspond, cannot use them to order SRA files by filesize. Only the spot metadata will be used to determine the layout.',
                            srr, len(reads_by_size), len(files_by_size))
                        fastq_filenames = None
                        fastq_file_sizes = None
                        use_bamtofastq = False
                        bam_filenames = None
                        bam_file_urls = None
                        bam_fastq_filenames = None
                        read_types = None
                        issues |= SraRunIssue.MISMATCHED_READ_SIZES
                else:
                    # this is extremely common, so it's not worth warning about it
                    logger.info(
                        '%s: No SRA file to order. Only the spot metadata will be used to determine the layout.',
                        srr)
                    fastq_filenames = None
                    fastq_file_sizes = None
                    use_bamtofastq = False
                    bam_filenames = None
                    bam_file_urls = None
                    bam_fastq_filenames = None
                    read_types = None
                    issues |= SraRunIssue.NO_SRA_FILES
            else:
                # this is extremely common, so it's not worth warning about it
                logger.info(
                    '%s: Number of bps per read are ambiguous: %s, cannot use them to order SRA files by filesize. Only the spot metadata will be used to determine the layout.',
                    srr, read_sizes)
                fastq_filenames = None
                fastq_file_sizes = None
                use_bamtofastq = False
                bam_filenames = None
                bam_file_urls = None
                bam_fastq_filenames = None
                read_types = None
                issues |= SraRunIssue.AMBIGUOUS_READ_SIZES

        elif len(sra_fastq_files) == 1:
            logger.info('%s: Single FASTQ file found, using it as a single-end dataset.', srr)
            fastq_filenames = [sf.attrib['filename'] for sf in sra_fastq_files]
            fastq_file_sizes = [int(sf.attrib['size']) for sf in sra_fastq_files]
            use_bamtofastq = False
            bam_filenames = [bf.attrib['filename'] for bf in sra_10x_bam_files]
            bam_file_urls = [bf.attrib['url'] for bf in sra_10x_bam_files]
            bam_fastq_filenames = None
            read_types = fastq_load_read_types

        else:
            issues |= SraRunIssue.INVALID_RUN
            logger.warning(
                '%s: No information found that can be used to order SRA files, ignoring that run.',
                srr)
            if include_invalid_runs:
                fastq_filenames = [sf.attrib['filename'] for sf in sra_fastq_files]
                fastq_file_sizes = [int(sf.attrib['size']) for sf in sra_fastq_files]
                use_bamtofastq = False
                bam_filenames = [bf.attrib['filename'] for bf in sra_10x_bam_files]
                bam_file_urls = [bf.attrib['url'] for bf in sra_10x_bam_files]
                result.append(SraRunMetadata(srx, srr,
                                             is_single_end=is_single_end,
                                             is_paired=is_paired,
                                             fastq_filenames=fastq_filenames,
                                             fastq_file_sizes=fastq_file_sizes,
                                             read_types=None,
                                             number_of_spots=None,
                                             average_read_lengths=None,
                                             fastq_load_options=None,
                                             use_bamtofastq=use_bamtofastq,
                                             bam_filenames=bam_filenames,
                                             bam_file_urls=bam_file_urls,
                                             bam_fastq_filenames=None,
                                             layout=[],
                                             issues=issues))
            continue

        try:
            layout = detect_layout(srr, fastq_filenames, fastq_file_sizes, spot_read_lengths, read_types, is_single_end,
                                   is_paired)
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
                                     use_bamtofastq=use_bamtofastq,
                                     bam_filenames=bam_filenames,
                                     bam_file_urls=bam_file_urls,
                                     bam_fastq_filenames=bam_fastq_filenames,
                                     layout=layout,
                                     issues=issues))
    return result

def read_bam_header(srr, filename, url):
    """Read and cache the header of a SRA BAM file."""
    bam_header_file = join(cfg.OUTPUT_DIR, sra_config.bam_headers_cache_dir, srr + '.bam-header.txt')
    if os.path.exists(bam_header_file):
        logger.info('%s: Using cached 10x BAM header from %s...', srr, bam_header_file)
    else:
        logger.info('%s: Reading header from 10x BAM file %s from %s to %s...', srr,
                    filename, url, bam_header_file)
        os.makedirs(os.path.dirname(bam_header_file), exist_ok=True)
        with open(bam_header_file, 'w') as f:
            # FIXME: use requests
            # res = requests.get(bam_file.attrib['url'], stream=True)
            with subprocess.Popen([sra_config.curl_bin, url], stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL) as curl_proc:
                try:
                    subprocess.run([sra_config.samtools_bin, 'head'],
                                   stdin=curl_proc.stdout, stdout=f, text=True, check=True)
                finally:
                    curl_proc.terminate()
    return bam_header_file

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

    @property
    def output_dir(self):
        return join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx, self.srr)

    def on_success(self):
        # cleanup SRA archive once dumped if it's still hanging around
        prefetch_task = self.requires()
        remove_task_output(prefetch_task)
        return super().on_success()

    def run(self):
        yield sratoolkit.FastqDump(input_file=self.input().path,
                                   output_dir=self.output_dir,
                                   split='files',
                                   metadata=self.metadata)
        if not self.complete():
            files = '\n\t'.join(glob(join(self.output_dir, '*.fastq.gz')))
            raise RuntimeError(
                f'{repr(self)} was not completed after successful fastq-dump execution; are the output files respecting the following layout: {self.layout}?\n\t{files}')

    def output(self):
        return DownloadRunTarget(run_id=self.srr,
                                 files=[join(self.output_dir, self.srr + '_' + str(i + 1) + '.fastq.gz') for i in
                                        range(len(self.layout))],
                                 layout=self.layout,
                                 output_dir=self.output_dir)

class EmptyRunInfoError(Exception):
    pass

class DownloadSraFile(ScheduledExternalProgramTask):
    """Download an SRA file."""
    srr: str = luigi.Parameter(description='SRA run identifier')
    filename: str = luigi.Parameter(description='SRA filename')
    file_url: str = luigi.Parameter(description='SRA file URL')

    scheduler_partition = 'Wormhole'

    _tmp_filename: str = None

    @property
    def resources(self):
        r = super().resources
        r.update({'prefetch_jobs': 1})
        return r

    def run(self):
        with self.output().temporary_path() as self._tmp_filename:
            super().run()

    def program_args(self):
        return ['curl', self.file_url, '-o', self._tmp_filename]

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.DATA, 'sra-files', self.srr, self.filename))

@requires(DownloadSraFile)
class DumpBamRun(TaskWithMetadataMixin, luigi.Task):
    srx: str = luigi.Parameter()
    layout: list[str] = luigi.ListParameter()

    # inherited
    srr: str
    filename: str
    file_url: str

    _sequencing_layout = None

    @property
    def sequencing_layout(self) -> dict[str, dict[int, list[SequencingFileType]]]:
        if self._sequencing_layout is None:
            with open(read_bam_header(self.srr, self.filename, self.file_url), 'r') as f:
                self._sequencing_layout = read_sequencing_layout_from_10x_bam_header(f)
        return self._sequencing_layout

    @property
    def output_dir(self):
        return join(cfg.OUTPUT_DIR, cfg.DATA, 'sra', self.srx, self.srr)

    def run(self):
        yield cellranger.BamToFastq(input_file=self.input().path,
                                    output_dir=self.output_dir,
                                    cpus=4,
                                    scheduler_extra_args=['--constraint', 'thrd64'])

        # The BAM header does not indicate the last digits in the filename
        # rename _XXX.fastq.gz to _001.fastq.gz
        for fastq_file in glob(join(self.output_dir, '*/*.fastq.gz')):
            if not fastq_file.endswith('_001.fastq.gz'):
                new_name = fastq_file.rsplit('_', maxsplit=1)[0] + '_001.fastq.gz'
                logger.info('Renaming %s to %s.', fastq_file, new_name)
                os.rename(fastq_file, new_name)

        if not self.complete():
            raise RuntimeError('Expected output files from bamtofastq were not produced:\n\t' + '\n\t'.join(
                f for rt in self.output() for f in rt.files))

    def output(self):
        return [DownloadRunTarget(run_id=f'{self.srr}_{flowcell_id}_L{lane_id:03}',
                                  files=[join(self.output_dir, get_fastq_filename(flowcell_id, lane_id, read_type))
                                         for read_type in lane],
                                  layout=self.layout,
                                  output_dir=self.output_dir)
                for flowcell_id, flowcell in self.sequencing_layout.items()
                for lane_id, lane in flowcell.items()]

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
    retry_count = 3

    def run(self):
        if self.output().is_stale():
            logger.info('%s is stale, redownloading...', self.output())
        meta = retrieve_sra_metadata(self.srx, format='xml')
        # basic validation
        ET.fromstring(meta)
        with self.output().open('w') as f:
            f.write(meta)

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

        runs = []

        for row in meta:
            if row.use_bamtofastq:
                for bam_file, bam_url in zip(row.bam_filenames, row.bam_file_urls):
                    runs.append(DumpBamRun(srx=self.srx, srr=row.srr, filename=bam_file, file_url=bam_url,
                                           layout=[ft.name for ft in row.layout], metadata=metadata))
            else:
                runs.append(
                    DumpSraRun(srr=row.srr, srx=self.srx, layout=[ft.name for ft in row.layout], metadata=metadata))

        yield runs

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
