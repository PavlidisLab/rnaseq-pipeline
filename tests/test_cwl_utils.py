from rnaseq_pipeline.tasks import CountExperiment
from rnaseq_pipeline.cwl_utils import *
import yaml

def test_sp():
    pkgs = gen_software_packages()
    assert any(pkg['package'] == 'sratoolkit' for pkg in pkgs)
    assert any(pkg['package'] == 'STAR' for pkg in pkgs)
    assert any(pkg['package'] == 'RSEM' for pkg in pkgs)

def test_workflow_requirements():
    workflow_reqs = gen_workflow_requirements()
    assert len(workflow_reqs) > 0
    assert any(req['class'] == 'SoftwareRequirement' for req in workflow_reqs)

def test_gen_workflow():
    workflow = gen_workflow(CountExperiment('GSE75484', source='gemma', reference_id='mm10_ncbi'))
    assert workflow['class'] == 'Workflow'
    assert 'cwlVersion' in workflow
    assert 'inputs' in workflow
    assert 'outputs' in workflow
    assert 'steps' in workflow
    assert 'requirements' in workflow
