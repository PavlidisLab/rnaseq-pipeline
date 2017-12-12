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
    echo "  $0 $JOB $MODES --gse=$GSE [other args]"
    exit -1
fi

echo "INFO: ARGS:" $@
JOB=$1
MODES=$2
shift 
shift 

echo "Scheduling $JOB job for $@"

export MODES=$MODES
export DATA=$DATA
export QUANTDIR=$QUANTDIR
export RESULTDIR=$RESULTDIR
export COUNTDIR=$COUNTDIR

echo @ $@
# Assuming the --gse argument is required.
export CURRENTGSE=$(echo $@ \
						| tr " " "\n" \
						| grep "\-\-gse\=" \
 						| sed 's|\-\-gse\=||g' \
						| head -n1)

echo "Current GSE="$CURRENTGSE

MODES=$MODES PYTHONPATH='.' luigi --scheduler-port $SCHEDULER_PORT --module tasks $JOB $@