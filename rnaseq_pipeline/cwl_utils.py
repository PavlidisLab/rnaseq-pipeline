"""
Utilities for dumping a CWL representation of a Luigi workflow.
"""

import inspect
from os.path import join
from subprocess import check_output
from warnings import warn

import bioluigi
import luigi
from luigi.task import flatten
from luigi.contrib.external_program import ExternalProgramTask

from .config import rnaseq_pipeline

bioluigi_cfg = bioluigi.config.bioluigi()
cfg = rnaseq_pipeline()

def gen_command_line_tool(task):
    return {'class': 'CommandLineTool',
            'baseCommand': task.program_args()[0],
            'arguments': task.program_args()[1:]}

def gen_workflow_inputs(task):
    return [{'type': 'File', 'location': inp.path} for inp in flatten(task.input())]

def gen_workflow_outputs(task):
    return [{'type': 'File', 'location': out.path} for out in flatten(task.output())]

def gen_inputs(task):
    inputs = []
    for inp in flatten(task.input()):
        if isinstance(inp, luigi.LocalTarget):
            inputs.append(inp.path)
        else:
            inputs.append({'id': repr(inp)})
    return inputs

def gen_outputs(task):
    outputs = []
    for out in flatten(task.output()):
        if isinstance(out, luigi.LocalTarget):
            outputs.append(out.path)
        else:
            outputs.append({'id': repr(out)})
    return outputs

def gen_workflow_step(task):
    workflow_step = {'id': repr(task),
                     'in': gen_inputs(task),
                     'out': gen_outputs(task)}
    if isinstance(task, ExternalProgramTask):
        workflow_step['run'] = gen_command_line_tool(task)
    else:
        workflow_step['run'] = inspect.getsource(task.run)
    return workflow_step

def gen_software_packages():
    return [{'package': 'sratoolkit',
             'version': check_output([bioluigi_cfg.fastqdump_bin, '--version']).split()[-1]},
            {'package': 'STAR',
             'version': check_output(['STAR', '--version']).rstrip()},
            {'package': 'RSEM',
             'version': check_output([join(cfg.RSEM_DIR, 'rsem-calculate-expression'), '--version']).split()[-1]}]

def gen_workflow_requirements():
    return [{'class': 'SoftwareRequirement',
             'packages': gen_software_packages()}]

def gen_workflow(goal_task):
    """
    Produce a CWL representation of the given task.
    """
    workflow = {'cwlVersion': 'v1.1',
                'class': 'Workflow',
                'requirements': gen_workflow_requirements(),
                'inputs': [],
                'outputs': gen_workflow_outputs(goal_task),
                'steps': []}

    # walk the workflow top to bottom
    fringe = [goal_task]

    # set of already emitted workflow steps identifiers
    emitted_steps = set()

    while fringe:
        t = fringe.pop()

        workflow_step = gen_workflow_step(t)

        if not workflow_step['id'] in emitted_steps:
            workflow['steps'].insert(0, workflow_step)
            emitted_steps.add(workflow_step['id'])

        # leaf tasks might have some defined inputs although no specific
        # dependencies
        if not t.requires():
            workflow['inputs'].extend([inp for inp in gen_workflow_inputs(t) if inp not in workflow['inputs']])

        # static dependencies
        for dep in luigi.task.flatten(t.requires()):
            fringe.append(dep)

        # dynamic dependencies
        if inspect.isgeneratorfunction(t.run):
            if all(d.complete() for d in luigi.task.flatten(t.requires())):
                for chunk in t.run():
                    for dep in luigi.task.flatten(chunk):
                        fringe.append(dep)
            else:
                warn('Not checking {} for dynamic dependencies: it is not satisfied.'.format(repr(t)))

    return workflow
