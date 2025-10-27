import tempfile
from datetime import timedelta
from time import sleep

import pytest

from rnaseq_pipeline.targets import GemmaDatasetHasBatch, GemmaDataVectorType, ExpirableLocalTarget, \
    GemmaDatasetQuantitationType

@pytest.mark.skip('This test requires credentials.')
def test_gemma_dataset_has_batch():
    assert GemmaDatasetHasBatch('GSE110256').exists()

def test_gemma_dataset_quantitation_type():
    assert GemmaDatasetQuantitationType('GSE2018', vector_type=GemmaDataVectorType.RAW).exists()
    assert GemmaDatasetQuantitationType('GSE2018', 'rma value').exists()
    assert not GemmaDatasetQuantitationType('GSE2018', 'rma value 2').exists()

    assert GemmaDatasetQuantitationType('GSE2018', vector_type=GemmaDataVectorType.PROCESSED).exists()
    assert GemmaDatasetQuantitationType('GSE2018', 'rma value - Processed version').exists()

    assert not GemmaDatasetQuantitationType('GSE2018', vector_type=GemmaDataVectorType.SINGLE_CELL).exists()

def test_expirable_local_target():
    with tempfile.TemporaryDirectory() as tmp_dir:
        t = ExpirableLocalTarget(tmp_dir + '/test', ttl=timedelta(seconds=1))
        assert not t.exists()
        with t.open('w') as f:
            pass
        assert t.exists()
        sleep(1)
        assert not t.exists()

def test_expirable_local_target_with_float_ttl():
    with tempfile.TemporaryDirectory() as tmp_dir:
        t = ExpirableLocalTarget(tmp_dir + '/test', ttl=1.0)
        assert not t.exists()
        with t.open('w') as f:
            pass
        assert t.exists()
        sleep(1)
        assert not t.exists()
