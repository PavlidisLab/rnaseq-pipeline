from rnaseq_pipeline.config import rnaseq_pipeline
from rnaseq_pipeline.tasks import *

cfg = rnaseq_pipeline()

def test_align_sample_task():
    task = AlignSample('GSE', 'GSM', reference_id='hg38_ncbi', scope='genes')
    assert task.output().path == join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, 'hg38_ncbi', 'GSE', 'GSM.genes.results')

def test_gemma_task():
    gemma_task = GemmaTask('GSE110256')
    assert gemma_task.taxon == 'mouse'
    assert gemma_task.accession == 'GSE110256'
    assert gemma_task.external_database == 'GEO'
