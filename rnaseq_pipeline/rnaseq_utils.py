"""
Utilities for inferring layouts of RNA-Seq data based on original filenames
"""
import enum
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

class SequencingFileType(enum.Enum):
    """Type of RNA-Seq file"""
    I1 = 1
    I2 = 2
    R1 = 3
    R2 = 4
    R3 = 5
    R4 = 6

def detect_layout(run_id: str, filenames: Optional[list[str]],
                  file_sizes: Optional[list[int]] = None,
                  average_read_lengths: Optional[list[float]] = None,
                  is_single_end: bool = False, is_paired: bool = False):
    """Detects the layout of the sequencing run files based on their names and various additional information.

    :param run_id: Identifier for the run
    :param filenames: List of filenames, if known
    :param file_sizes: List of file sizes, if known
    :param average_read_lengths: List of read lengths (average if variable) for each file, if known
    :param is_single_end: Indicate if the sequencing data is single-end (i.e. only R1 is expected to be present).
    :param is_paired: Indicate if the sequencing data is paired (i.e. R1 and R2 are expected to be present), this will
    be used to resolve ambiguities.
    :raises ValueError: If the layout cannot be determined from the filenames.
    """

    if filenames:
        if layout := detect_bcl2fastq_name(run_id, filenames):
            logger.info('%s: Inferred file types: %s from file names conforming to bcl2fastq output: %s.', run_id,
                        '|'.join(l.name for l in layout), ', '.join(filenames))
            return layout

        if layout := detect_common_fastq_name(run_id, filenames):
            logger.info('%s: Inferred file types: %s from file names conforming to a common output: %s.', run_id,
                        '|'.join(l.name for l in layout), ', '.join(filenames))
            return layout

        if layout := detect_fallback_fastq_name(run_id, filenames):
            logger.warning('%s: Inferred file types: %s from file names with fallback name patterns: %s. This is highly inaccurate.',
                           run_id, '|'.join(l.name for l in layout), ', '.join(filenames))
            return layout

        number_of_files = len(filenames)
    else:
        number_of_files = len(average_read_lengths)

    # assume single-end read if only one file is present
    if number_of_files == 1:
        if is_paired:
            raise ValueError(
                f'Expected the sequencing data for {run_id} to be paired, but only one file is present.')
        return [SequencingFileType.R1]

    # assume paired ends if two files are present
    if number_of_files == 2:
        if is_single_end:
            return order_layout_by_size_information(run_id, [SequencingFileType.I1, SequencingFileType.R1],
                                                    file_sizes, average_read_lengths)
        else:
            return [SequencingFileType.R1, SequencingFileType.R2]

    if number_of_files == 3:
        if is_single_end:
            return order_layout_by_size_information(run_id, [SequencingFileType.I1, SequencingFileType.I2,
                                                             SequencingFileType.R1], file_sizes,
                                                    average_read_lengths)
        else:
            return order_layout_by_size_information(run_id, [SequencingFileType.I1, SequencingFileType.R1,
                                                             SequencingFileType.R2], file_sizes,
                                                    average_read_lengths)

    if number_of_files == 4:
        if is_single_end:
            raise ValueError(
                f'Expected the sequencing data for {run_id} to be single-ended, but four files are present.')
        return order_layout_by_size_information(run_id, [SequencingFileType.I1, SequencingFileType.I2,
                                                         SequencingFileType.R1, SequencingFileType.R2],
                                                file_sizes,
                                                average_read_lengths)

    raise ValueError(
        f'Unable to detect sequencing layout for {run_id} from: {filenames=} {file_sizes=} {average_read_lengths=} {is_single_end=} {is_paired=}')

def detect_bcl2fastq_name(run_id, filenames):
    # try to detect the file types based on the filenames
    # from bcl2fastq manual, this is the expected format of the filenames:
    # <sample name>_<barcode sequence>_L<lane>_R<read number>_<set number>.fastq.gz
    bcl2fastq_name_pattern = re.compile(r'(.+)_L0*(\d+)_([RI])(\d)_\d+\.fastq(\.gz)?')

    detected_types = []
    for filename in filenames:
        if match := bcl2fastq_name_pattern.match(filename):
            sample_name = match.group(1)
            lane = match.group(2)
            read_type = match.group(3)
            read_number = int(match.group(4))
            if read_type == 'I' and read_number == 1:
                dt = SequencingFileType.I1
            elif read_type == 'I' and read_number == 2:
                dt = SequencingFileType.I2
            elif read_type == 'R' and read_number == 1:
                dt = SequencingFileType.R1
            elif read_type == 'R' and read_number == 2:
                dt = SequencingFileType.R2
            elif read_type == 'R' and read_number == 3:
                dt = SequencingFileType.R3
            elif read_type == 'R' and read_number == 4:
                dt = SequencingFileType.R4
            else:
                logger.warning('%s: Unrecognized read type: %s%d in %s.', run_id, read_type, read_number, filename)
                break
            detected_types.append(dt)

    if len(set(detected_types)) < len(detected_types):
        logger.warning("%s: Non-unique sequencing file type detected: %s from %s.", run_id, detected_types, filenames)
        return None
    elif len(detected_types) == len(filenames):
        return detected_types
    else:
        return None

def detect_common_fastq_name(run_id, filenames):
    """Flexible detection of sequencing file types based on common, but valid naming patterns."""
    simple_name_pattern = re.compile(r'(.+[._-])?([RIri])(\d)([._-].+)?\.(fastq|fq)(\.gz)?')

    detected_types = []
    for filename in filenames:
        if match := simple_name_pattern.match(filename):
            sample_name = match.group(1)
            read_type = match.group(2).upper()
            read_number = int(match.group(3))
            if read_type == 'I' and read_number == 1:
                dt = SequencingFileType.I1
            elif read_type == 'I' and read_number == 2:
                dt = SequencingFileType.I2
            elif read_type == 'R' and read_number == 1:
                dt = SequencingFileType.R1
            elif read_type == 'R' and read_number == 2:
                dt = SequencingFileType.R2
            elif read_type == 'R' and read_number == 3:
                dt = SequencingFileType.R3
            elif read_type == 'R' and read_number == 4:
                dt = SequencingFileType.R4
            else:
                logger.warning('%s: Unrecognized read type: %s%d in %s.', run_id, read_type, read_number, filename)
                break
            detected_types.append(dt)

    if len(set(detected_types)) < len(detected_types):
        logger.warning("%s: Non-unique sequencing file type detected: %s from %s.", run_id, detected_types, filenames)
        return None
    elif len(detected_types) == len(filenames):
        return detected_types
    else:
        return None

def detect_fallback_fastq_name(run_id, filenames):
    """Fallback detection of sequencing file types based on very simplistic substring matching."""
    detected_types = []

    # this is the most robust way of detecting file types
    if len(detected_types) == len(filenames):
        return detected_types

    # less robust detection, just lookup I1, I2, R1, R2 in filenames
    for filename in filenames:
        if 'I1' in filename:
            detected_types.append(SequencingFileType.I1)
        elif 'I2' in filename:
            detected_types.append(SequencingFileType.I2)
        elif 'R1' in filename:
            detected_types.append(SequencingFileType.R1)
        elif 'R2' in filename:
            detected_types.append(SequencingFileType.R2)
        elif 'R3' in filename:
            detected_types.append(SequencingFileType.R3)
        elif 'R4' in filename:
            detected_types.append(SequencingFileType.R4)
        else:
            break

    if len(set(detected_types)) < len(detected_types):
        logger.warning("%s: Non-unique sequencing file type detected: %s from %s.", run_id, detected_types, filenames)
        return None
    elif len(detected_types) == len(filenames):
        return detected_types
    else:
        return None

def order_layout_by_size_information(run_id: str,
                                     layout: list[SequencingFileType],
                                     file_sizes: Optional[list[int]],
                                     read_lengths: Optional[list[float]]):
    """
    Use information about file sizes and read lengths to guess the best order for a sequencing layout.

    This function essentially sorts the proposed layout in increasing order of read lengths (if available) or file size
    (as a fallback). This is usually used to
    """
    if read_lengths:
        ix = [item[0] for item in sorted(enumerate(read_lengths), key=lambda item: item[1])]
        return [layout[i] for i in ix]
    elif file_sizes:
        # this is less robust
        ix = [item[0] for item in sorted(enumerate(file_sizes), key=lambda item: item[1])]
        return [layout[i] for i in ix]
    else:
        raise ValueError(
            f'Cannot infer the proper order for the FASTQ files of {run_id} since no read lengths nor file sizes information was provided.')
