import pytest

from rnaseq_pipeline.webviewer import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_experiment_summary(client):
    res = client.get('/experiment/GSE87750')
    assert res.status == '200 OK'

@pytest.mark.skip()
def test_experiment_batch_info(client):
    res = client.get('/experiment/GSE87750/batch-info')
    assert res.status == '200 OK'
