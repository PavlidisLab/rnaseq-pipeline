import pytest

from rnaseq_pipeline.platforms import Platform, BgiPlatform, IlluminaPlatform

def test_illumina_platform():
    plt = Platform.from_geo_platform('GPL29601')
    assert plt.name == 'Illumina'
    assert plt.instrument == 'HiSeq 4000'

def test_bgi_platform():
    plt = Platform.from_geo_platform('GPL29559')
    assert plt.name == 'BGI'
    assert plt.instrument == 'BGISEQ-500'

def test_platform_retrieval_by_name_when_unknown_instrument():
    with pytest.raises(NotImplementedError):
        Platform.from_geo_platform('GPL29597')

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
