#!/bin/bash

echo "ARGS:" $@


JOB=$1
MODES=$2

shift
shift

if [ $# -lt 1 ]
  then
    GSE="GSE64978"
    JOB="ProcessGSE"
    MODES="(Optional)distributed"
    echo "Incorrect arguments."
    echo "Example:"
    echo "  $0 $JOB $MODES [args]"
    exit -1
fi

echo "Scheduling $JOB job for $@"

export MODES=$MODES
MODES=$MODES PYTHONPATH='.' luigi --module tasks $JOB $@
