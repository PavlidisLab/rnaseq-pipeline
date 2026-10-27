import pytest

from rnaseq_pipeline.gemma import *

def test_gemma_api():
    gemma_api = GemmaApi()
    gemma_api.datasets('GSE110256')
    gemma_api.samples('GSE110256')

def test_gemma_task():
    task = GemmaCliTask(experiment_id='GSE110256')
    assert task.dataset_short_name == 'GSE110256'
    assert task.assay_type == GemmaAssayType.BULK_RNA_SEQ
    assert task.platform_short_name == 'Generic_mouse_ncbiIds'
    env = task.program_environment()
    assert 'JAVA_OPTS' in env
    assert 'JAVA_HOME' in env
    assert 'PATH' in env

@pytest.mark.skip('This dataset is not public yet.')
def test_fac_sorted_dataset():
    # FAC-sorted single-cell datasets are treated as single-cell like any
    # other; there is no longer a special case routing them to bulk.
    task = GemmaCliTask(experiment_id='GSE232833')
    assert task.assay_type == GemmaAssayType.SINGLE_CELL_RNA_SEQ
ASSAY_CATEGORY_URI = 'http://purl.obolibrary.org/obo/OBI_0000070'

def _gemma_2_annotation(category_uri, value_uri):
    # shape of a GET /rest/v2/datasets/{id}/annotations row on Gemma 2.0
    return {'category': 'assay', 'categoryUri': category_uri, 'value': 'x', 'valueUri': value_uri,
            'objectClass': 'ExperimentTag'}

def _gemma_1_annotation(category_uri, value_uri):
    # the same row on Gemma 1.x
    return {'className': 'assay', 'classUri': category_uri, 'termName': 'x', 'termUri': value_uri}

@pytest.mark.parametrize('make_annotation', [_gemma_2_annotation, _gemma_1_annotation])
@pytest.mark.parametrize('value_uri,expected', [
    ('http://purl.obolibrary.org/obo/OBI_0003090', GemmaAssayType.BULK_RNA_SEQ),
    ('http://purl.obolibrary.org/obo/OBI_0002631', GemmaAssayType.SINGLE_CELL_RNA_SEQ),
    ('http://purl.obolibrary.org/obo/OBI_0001463', GemmaAssayType.MICROARRAY),
])
def test_assay_type_from_annotations(monkeypatch, make_annotation, value_uri, expected):
    annotations = [make_annotation('http://www.ebi.ac.uk/efo/EFO_0000635', 'http://purl.obolibrary.org/obo/UBERON_0000955'),
                   make_annotation(ASSAY_CATEGORY_URI, value_uri)]
    monkeypatch.setattr(gemma_api, 'dataset_annotations', lambda experiment_id: annotations)
    assert GemmaCliTask(experiment_id='GSE1').assay_type == expected

def test_assay_type_without_an_assay_tag(monkeypatch):
    annotations = [_gemma_2_annotation('http://www.ebi.ac.uk/efo/EFO_0000635', 'http://purl.obolibrary.org/obo/UBERON_0000955')]
    monkeypatch.setattr(gemma_api, 'dataset_annotations', lambda experiment_id: annotations)
    with pytest.raises(ValueError):
        GemmaCliTask(experiment_id='GSE1').assay_type
