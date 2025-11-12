from rnaseq_pipeline.rnaseq_utils import detect_common_fastq_name, SequencingFileType

R1, R2 = SequencingFileType.R1, SequencingFileType.R2

def test_detect_simple_fastq_name():
    assert detect_common_fastq_name('123', ['3543_OF1B_5-2-D6-F3-R1.fq', '3543_OF1B_5-2-D6-F3-R2.fq']) == [R1, R2]

def test_detect_name_with_lowercase():
    assert detect_common_fastq_name('SRR27810032', ['HLA00801R-I19.r1.fq.gz', 'HLA00801R-I19.r2.fq.gz']) == [R1, R2]
