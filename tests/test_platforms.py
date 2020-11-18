from rnaseq_pipeline.platforms import BgiPlatform, IlluminaPlatform

def test_bgi_platform_trim_single_end_reads():
    task = BgiPlatform().get_trim_single_end_reads_task('r1', 'r1_dest')

def test_illumin_platform_trim_single_end_reads():
    task = IlluminaPlatform().get_trim_single_end_reads_task('r1', 'r1_dest')
    assert 'AGATCGGAAGAGC' in task.program_args()

def test_illumin_platform_trim_paired_reads():
    task = IlluminaPlatform().get_trim_paired_reads_task('r1', 'r2', 'r1_dest', 'r2_dest')
    assert 'AGATCGGAAGAGC' in task.program_args()
