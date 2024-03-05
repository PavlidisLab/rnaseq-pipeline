import tempfile

from datetime import timedelta
from time import sleep
from rnaseq_pipeline.targets import GemmaDatasetPlatform, GemmaDatasetHasBatch, ExpirableLocalTarget

def test_gemma_targets():
    assert GemmaDatasetHasBatch('GSE110256').exists()
    assert GemmaDatasetPlatform('GSE110256', 'Generic_mouse_ncbiIds').exists()

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
