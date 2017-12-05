#!/bin/bash
set -eu
source ../etc/load_configs.sh

if [ $# -lt 1 ]
  then
    GSE="GSE64978"
    JOB="ProcessGSE"
    MODES="mouse,distributed"
    echo "Incorrect arguments."
    echo "Example:"
    echo "  $0 $JOB $MODES [args/GSE]"
    exit -1
fi

echo "INFO: ARGS:" $@
JOB=$1
MODES=$2
shift 
shift 

echo "Scheduling $JOB job for $@"

export MODES=$MODES
export QUANTDIR=$QUANTDIR
export RESULTDIR=$RESULTDIR
export COUNTDIR=$COUNTDIR

MODES=$MODES PYTHONPATH='.' luigi --scheduler-port $SCHEDULER_PORT --module tasks $JOB $@
