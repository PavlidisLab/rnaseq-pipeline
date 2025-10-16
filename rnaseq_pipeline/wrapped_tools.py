"""
This module provides various "wrapped" tools that improve the efficiency of the tools that the pipeline uses in various
fashions.

The most common use case is to copy large reference files to a local scratch directory on the compute node, and
coordinate its copy/removal with a lockfile.
"""

import fcntl
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from os.path import join, dirname, basename

import luigi
from luigi.contrib.external_program import ExternalProgramRunContext

class WrappedToolsConfig(luigi.Config):
    cellranger_bin: str = luigi.Parameter()
    rsem_calculate_expression_bin: str = luigi.Parameter()

cfg = WrappedToolsConfig()

@contextmanager
def lockf(lockfile, exclusive=False):
    if not os.path.exists(lockfile):
        with open(lockfile, 'w'):
            pass
    with open(lockfile, 'w' if exclusive else 'r') as f:
        fcntl.lockf(f.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH, 0)
        try:
            yield f
        finally:
            fcntl.lockf(f.fileno(), fcntl.LOCK_UN, 0)

def copy_directory_to_local_scratch(from_path):
    """Copy a directory to a local scratch directory. Return the new directory (local) and a lockfile that can be used to """
    reference_name = basename(from_path)
    new_dir = join(tempfile.gettempdir(), 'rnaseq-pipeline/references-single-cell', reference_name)
    lockfile = new_dir + '.lock'
    os.makedirs(dirname(new_dir), exist_ok=True)
    if not os.path.exists(new_dir):
        print('Copying ' + from_path + ' to a local directory ' + new_dir + '...')
        with lockf(lockfile, exclusive=True):
            with tempfile.TemporaryDirectory(prefix=basename(new_dir), dir=dirname(new_dir)) as tmp_dir:
                tmp_dir = join(tmp_dir, basename(new_dir))
                shutil.copytree(from_path, tmp_dir)
                os.rename(tmp_dir, new_dir)
    else:
        print('Reusing existing local reference directory ' + new_dir + '...')
    return new_dir, lockfile

def move_directory(from_dir, to_dir):
    print(f'Moving {from_dir} to {to_dir}...')
    if os.path.exists(to_dir):
        print(f'Destination {to_dir} already exists, removing it first...')
        shutil.rmtree(to_dir)
    if os.path.exists(from_dir):
        shutil.move(from_dir, to_dir)

def subprocess_run(args, **kwargs):
    proc = subprocess.Popen(args, **kwargs)
    with ExternalProgramRunContext(proc):
        proc.wait()
    return proc.returncode

def rsem_calculate_expression_wrapper():
    """Wrapper script for RSEM that copies the reference to a local temporary directory."""
    args = sys.argv.copy()
    args[0] = cfg.rsem_calculate_expression_bin
    if len(args) > 2 and os.path.isdir(args[-2]):
        # copy the reference to local scratch
        ref_dir = args[-2]
        new_dir, lockfile = copy_directory_to_local_scratch(ref_dir)
        args[-2] = new_dir
        with lockf(lockfile) as f:
            print('Final command: ' + ' '.join(args))
            os.set_inheritable(f.fileno(), True)
            os.execv(args[0], args[1:])
    else:
        print('Final command: ' + ' '.join(args))
        os.execv(args[0], args[1:])

def cellranger_wrapper():
    args = sys.argv.copy()
    args[0] = cfg.cellranger_bin
    lockfile = None
    output_dir = None
    with tempfile.TemporaryDirectory(prefix='cellranger-') as temp_dir:
        print('Created a temporary directory for Cell Ranger execution: ' + temp_dir)
        temp_output_dir = join(temp_dir, 'cellranger')
        for i, arg in enumerate(args):
            if arg == '--transcriptome':
                new_dir, lockfile = copy_directory_to_local_scratch(args[i + 1])
                args[i + 1] = new_dir
            elif arg.startswith('--transcriptome='):
                new_dir, lockfile = copy_directory_to_local_scratch(arg.removeprefix('--transcriptome='))
                args[i] = '--transcriptome=' + new_dir
            elif arg == '--output-dir':
                output_dir = args[i + 1]
                args[i + 1] = temp_output_dir
            elif arg.startswith('--output-dir='):
                output_dir = arg.removeprefix('--output-dir=')
                args[i] = '--output-dir=' + temp_output_dir
        print('Final command: ' + ' '.join(args))

        if lockfile:
            with lockf(lockfile, exclusive=False) as f:
                returncode = subprocess_run(args, cwd=temp_dir)
        else:
            returncode = subprocess_run(args, cwd=temp_dir)

        if output_dir:
            move_directory(join(temp_output_dir, 'outs'), join(output_dir, 'outs'))

        sys.exit(returncode)
