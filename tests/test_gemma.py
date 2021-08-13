from rnaseq_pipeline.gemma import *

def test_gemma_api():
    gemma_api = GemmaApi()
    gemma_api.datasets('GSE110256')
    gemma_api.samples('GSE110256')
