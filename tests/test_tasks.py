import pytest

from gemma import GemmaTaskMixin
from rnaseq_pipeline.sources.geo import match_geo_platform
from rnaseq_pipeline.tasks import *

cfg = rnaseq_pipeline()

def test_illumina_platform():
    plt = match_geo_platform('GPL29601')
    assert plt.name == 'Illumina'
    assert plt.instrument == 'HiSeq 4000'

def test_illumina_hiseq_x_platform():
    plt = match_geo_platform('GPL20795')
    assert plt.name == 'Illumina'
    assert plt.instrument == 'HiSeq X Ten'

def test_illumina_nextseq_550_platform():
    plt = match_geo_platform('GPL21626')
    assert plt.name == 'Illumina'
    assert plt.instrument == 'NextSeq 550'

def test_bgi_platform():
    plt = match_geo_platform('GPL29559')
    assert plt.name == 'BGI'
    assert plt.instrument == 'BGISEQ-500'

def test_bgi_dnbseq_g400_platform():
    plt = match_geo_platform('GPL28038')
    assert plt.name == 'BGI'
    assert plt.instrument == 'DNBSEQ-G400'

def test_platform_retrieval_by_name_when_unknown_instrument():
    with pytest.raises(NotImplementedError):
        match_geo_platform('GPL29597')

def test_align_sample_task():
    task = AlignSample('GSE', 'GSM', reference_id='hg38_ncbi', taxon='human', scope='genes')
    assert task.output().path == join(cfg.OUTPUT_DIR, cfg.ALIGNDIR, 'hg38_ncbi', 'GSE', 'GSM.genes.results')
    assert task.walltime == datetime.timedelta(days=1)

def test_gemma_task_mixin():
    class GemmaTask(GemmaTaskMixin, luigi.Task):
        pass

    gemma_task = GemmaTask('GSE110256')
    assert gemma_task.taxon == 'mouse'
    assert gemma_task.accession == 'GSE110256'
    assert gemma_task.external_database == 'GEO'
