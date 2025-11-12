from os.path import join, dirname

from rnaseq_pipeline import SequencingFileType, get_fastq_filenames_for_10x_sequencing_layout
from rnaseq_pipeline.tenx_utils import read_sequencing_layout_from_10x_bam_header

test_data_dir = join(dirname(__file__), 'data')

def test():
    with open(join(test_data_dir, 'YY1R.bam-header.txt')) as f:
        l = read_sequencing_layout_from_10x_bam_header(f)
        assert len(l) == 3
        assert 's10_MissingLibrary_1_HG3T5BGX2' in l
        assert 's10_MissingLibrary_1_HHJT3BGX2' in l
        assert 's10_MissingLibrary_1_HYHJ7BGXY' in l
        for lane_id, lane in l['s10_MissingLibrary_1_HG3T5BGX2'].items():
            assert lane == [SequencingFileType.I1, SequencingFileType.R1, SequencingFileType.R2]
    assert get_fastq_filenames_for_10x_sequencing_layout(l) == [
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L001_I1_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L001_R1_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L001_R2_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L002_I1_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L002_R1_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L002_R2_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L003_I1_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L003_R1_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L003_R2_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L004_I1_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L004_R1_001.fastq.gz',
        's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L004_R2_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L001_I1_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L001_R1_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L001_R2_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L002_I1_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L002_R1_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L002_R2_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L003_I1_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L003_R1_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L003_R2_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L004_I1_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L004_R1_001.fastq.gz',
        's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L004_R2_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L001_I1_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L001_R1_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L001_R2_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L002_I1_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L002_R1_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L002_R2_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L003_I1_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L003_R1_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L003_R2_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L004_I1_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L004_R1_001.fastq.gz',
        's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L004_R2_001.fastq.gz'
    ]
