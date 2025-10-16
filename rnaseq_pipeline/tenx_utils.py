"""
Utilities for handling 10x RNA sequencing data.
"""
import re

from .rnaseq_utils import SequencingFileType

bam2fastq_pattern = re.compile(r'10x_bam_to_fastq:(.+)\(.+\)')

def read_sequencing_layout_from_10x_bam_header(f) -> dict[str, dict[int, list[SequencingFileType]]]:
    """Read 10x BAM header and extract the sequencing layout.

    The header can be extracted with `samtools head`.
    :return: A mapping of flowcell IDs to a mapping of lane IDs to a list of SequencingFileType.
    """
    flowcells = {}
    bam_read_types = []
    for line in f:
        line = line.rstrip()
        tag_name, tag_value = line.split("\t", maxsplit=1)
        if tag_name == '@RG':
            tag_value_dict = {k: v for (k, v) in [t.split(':', maxsplit=1) for t in tag_value.split('\t')]}
            if 'PU' in tag_value_dict:
                *flowcell_id, lane_id = tag_value_dict['PU'].split(':')
                flowcell_id = '_'.join(flowcell_id)
                if flowcell_id not in flowcells:
                    flowcells[flowcell_id] = []
                flowcells[flowcell_id].append(int(lane_id))
        elif tag_name == '@CO' and tag_value.startswith('user command line:'):
            bam_read_types = []
        elif tag_name == '@CO' and (m := bam2fastq_pattern.match(tag_value)):
            assert bam_read_types is not None
            bam_read_types.append(SequencingFileType[m.group(1)])

    # map lanes to layouts
    return {fc: {lane_id: bam_read_types for lane_id in lanes} for fc, lanes in flowcells.items()}

def get_fastq_filename(flowcell, lane, read_type: SequencingFileType):
    return f'{flowcell}/bamtofastq_S1_L{lane:03}_{read_type.name}_001.fastq.gz'

def get_fastq_filenames_for_10x_sequencing_layout(flowcells):
    return [get_fastq_filename(flowcell, lane, rt)
            for flowcell, lanes in flowcells.items()
            for lane, read_types in lanes.items()
            for rt in read_types]
