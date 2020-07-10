from rnaseq_pipeline.targets import GemmaDatasetPlatform, GemmaDatasetFactor

def test_gemma_targets():
    assert GemmaDatasetFactor('GSE110256', 'batch').exists()
    assert GemmaDatasetPlatform('GSE110256', 'Generic_mouse_ncbiIds').exists()
