from rnaseq_pipeline.platforms import BgiPlatform, IlluminaPlatform, IlluminaNexteraPlatform

def test_bgi_platform_trim_single_end_reads():
    task = BgiPlatform('BGISEQ-500').get_trim_single_end_reads_task('r1', 'r1_dest')
    assert 'AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA' in task.program_args()

def test_bgi_platform_trim_paired_end_reads():
    task = BgiPlatform('BGISEQ-500').get_trim_paired_reads_task('r1', 'r2', 'r1_dest', 'r2_dest')
    assert 'AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA' in task.program_args()
    assert 'AAGTCGGATCGTAGCCATGTCGTTCTGTGAGCCAAGGAGTTG' in task.program_args()

def test_illumin_platform_trim_single_end_reads():
    task = IlluminaPlatform('HiSeq 2500').get_trim_single_end_reads_task('r1', 'r1_dest')
    assert 'AGATCGGAAGAGC' in task.program_args()

def test_illumin_platform_trim_paired_reads():
    task = IlluminaPlatform('HiSeq 2500').get_trim_paired_reads_task('r1', 'r2', 'r1_dest', 'r2_dest')
    assert 'AGATCGGAAGAGC' in task.program_args()

def test_illumina_nextera_trim_paired_reads():
    task = IlluminaNexteraPlatform('HiSeq 2500').get_trim_single_end_reads_task('r1', 'r1_dest')
    assert 'CTGTCTCTTATACACATCT' in task.program_args()
