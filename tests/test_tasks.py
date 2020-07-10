from rnaseq_pipeline.config import core
from rnaseq_pipeline.tasks import *

cfg = core()

def test_align_sample_task():
    task = AlignSample('GSE', 'GSM', reference_id='hg38_ncbi', scope='genes')
    assert task.output().path == join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, 'hg38_ncbi', 'GSE', 'GSM.genes.results')
