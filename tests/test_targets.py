from rnaseq_pipeline.targets import GemmaDatasetPlatform, GemmaDatasetHasBatch

def test_gemma_targets():
    assert GemmaDatasetHasBatch('GSE110256').exists()
    assert GemmaDatasetPlatform('GSE110256', 'Generic_mouse_ncbiIds').exists()
