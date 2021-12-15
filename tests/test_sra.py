import pytest

from rnaseq_pipeline.sources.sra import DownloadSraExperimentRunInfo, DownloadSraProjectRunInfo, EmptyRunInfoError

def test_download_sra_experiment_run_info():
    task = DownloadSraExperimentRunInfo(srx='SRX12752257')
    task.run()
    contents = task.output().open('r').read()
    assert contents
    assert task.complete()

def test_empty_sra_file_raises_exception():
    fake_sra_accession = 'SRX129093021'
    task = DownloadSraExperimentRunInfo(srx=fake_sra_accession)
    with pytest.raises(EmptyRunInfoError, match=fake_sra_accession):
        task.run()
    assert not task.output().exists()
    assert not task.complete()

def test_download_sra_project_run_info():
    task = DownloadSraProjectRunInfo(srp='SRP342859')
    task.run()
    contents = task.output().open('r').read()
    assert contents
    assert task.complete()
