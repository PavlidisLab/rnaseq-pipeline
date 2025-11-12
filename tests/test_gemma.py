import pytest

from rnaseq_pipeline.gemma import *

def test_gemma_api():
    gemma_api = GemmaApi()
    gemma_api.datasets('GSE110256')
    gemma_api.samples('GSE110256')

def test_gemma_task():
    task = GemmaCliTask(experiment_id='GSE110256')
    assert task.dataset_short_name == 'GSE110256'
    assert task.assay_type == GemmaAssayType.BULK_RNA_SEQ
    assert task.platform_short_name == 'Generic_mouse_ncbiIds'
    env = task.program_environment()
    assert 'JAVA_OPTS' in env
    assert 'JAVA_HOME' in env
    assert 'PATH' in env

@pytest.mark.skip('This dataset is not public yet.')
def test_fac_sorted_dataset():
    task = GemmaCliTask(experiment_id='GSE232833')
    assert task.assay_type == GemmaAssayType.BULK_RNA_SEQ