import argparse
import sys
import os
from contextlib import contextmanager

import luigi
import luigi.cmdline

from rnaseq_pipeline.tasks import SubmitExperimentToGemma, SubmitExperimentsFromGoogleSpreadsheetToGemma, \
    SubmitExperimentBatchInfoToGemma

@contextmanager
def umask(umask):
    print(f'Setting umask to 0x{umask:03o}')
    prev_umask = os.umask(umask)
    try:
        yield None
    finally:
        print(f'Restoring umask to 0x{prev_umask:03o}')
        os.umask(prev_umask)

def parse_octal(s):
    return int(s, 8)

def run_luigi_task(task, args):
    with umask(args.umask):
        luigi.build([task], workers=args.workers, detailed_summary=True, local_scheduler=args.local_scheduler)

def run(args):
    with umask(0o002):
        luigi.run(args)

def submit_experiment(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment-id', required=True, help='Experiment ID to submit to Gemma')
    parser.add_argument('--rerun', action='store_true', default=False, help='Rerun the experiment')
    parser.add_argument('--priority', type=int, default=100)
    parser.add_argument('--umask', type=parse_octal, default='002',
                        help='Set a umask (defaults to 002 to make created files group-writable)')
    parser.add_argument('--workers', type=int, default=30, help='Number of workers to use (defaults to 30)')
    parser.add_argument('--local-scheduler', action='store_true', default=False)
    args = parser.parse_args(argv)
    run_luigi_task(SubmitExperimentToGemma(experiment_id=args.experiment_id, rerun=args.rerun, priority=args.priority),
                   args)

def submit_experiment_batch_info(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment-id', required=True, help='Experiment ID to submit to Gemma')
    parser.add_argument('--ignored-samples', nargs='+', default=[])
    parser.add_argument('--rerun', action='store_true', default=False, help='Rerun the experiment')
    parser.add_argument('--umask', type=parse_octal, default='002',
                        help='Set a umask (defaults to 002 to make created files group-writable)')
    parser.add_argument('--workers', type=int, default=30, help='Number of workers to use (defaults to 30)')
    parser.add_argument('--local-scheduler', action='store_true', default=False)
    args = parser.parse_args(argv)
    print(args.ignored_samples)
    run_luigi_task(
        SubmitExperimentBatchInfoToGemma(experiment_id=args.experiment_id, ignored_samples=args.ignored_samples,
                                         rerun=args.rerun), args)

def submit_experiments_from_gsheet(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--spreadsheet-id', required=True, help='Spreadsheet ID')
    parser.add_argument('--sheet-name', required=True, help='Sheet name')
    parser.add_argument('--umask', type=parse_octal, default='002',
                        help='Set a umask (defaults to 002 to make created files group-writable)')
    parser.add_argument('--workers', type=int, default=200, help='Number of workers to use (defaults to 200)')
    parser.add_argument('--ignore-priority', action='store_true', help='Ignore the priority column in the spreadsheet')
    parser.add_argument('--local-scheduler', action='store_true', default=False)
    args = parser.parse_args(argv)
    run_luigi_task(SubmitExperimentsFromGoogleSpreadsheetToGemma(args.spreadsheet_id, args.sheet_name,
                                                                 ignore_priority=args.ignore_priority), args)

def main():
    if len(sys.argv) < 2:
        print('Usage: rnaseq-pipeline-cli <command>')
        return 1
    command = sys.argv[1]
    if command == 'run':
        return run(sys.argv[2:])
    elif command == 'submit-experiment':
        return submit_experiment(sys.argv[2:])
    elif command == 'submit-experiment-batch-info':
        return submit_experiment_batch_info(sys.argv[2:])
    elif command == 'submit-experiments-from-gsheet':
        return submit_experiments_from_gsheet(sys.argv[2:])
    else:
        print(
            f'Unknown command {command}. Possible values are: submit-experiment, submit-experiment-batch-info, submit-experiments-from-gsheet.')
        return 1
