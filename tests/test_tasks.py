import pytest

from rnaseq_pipeline.config import rnaseq_pipeline
from rnaseq_pipeline.tasks import *

from rnaseq_pipeline.sources.geo import match_geo_platform

cfg = rnaseq_pipeline()

def test_illumina_platform():
    plt = match_geo_platform('GPL29601')
    assert plt.name == 'Illumina'
    assert plt.instrument == 'HiSeq 4000'

def test_bgi_platform():
    plt = match_geo_platform('GPL29559')
    assert plt.name == 'BGI'
    assert plt.instrument == 'BGISEQ-500'

def test_platform_retrieval_by_name_when_unknown_instrument():
    with pytest.raises(NotImplementedError):
        match_geo_platform('GPL29597')

def test_align_sample_task():
    task = AlignSample('GSE', 'GSM', reference_id='hg38_ncbi', scope='genes')
    assert task.output().path == join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, 'hg38_ncbi', 'GSE', 'GSM.genes.results')

def test_gemma_task():
    gemma_task = GemmaTask('GSE110256')
    assert gemma_task.taxon == 'mouse'
    assert gemma_task.accession == 'GSE110256'
    assert gemma_task.external_database == 'GEO'
