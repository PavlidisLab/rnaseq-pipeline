from rnaseq_pipeline.gemma import *
import os

def test_gemma_api():
    gemma_api = GemmaApi()
    gemma_api.datasets('GSE110256')
    gemma_api.samples('GSE110256')

def test_gemma_task():
    task = GemmaTask(experiment_id='GSE110256')
    env = task.program_environment()
    assert 'JAVA_OPTS' in env
    assert 'JAVA_HOME' in env
    assert 'PATH' in env
