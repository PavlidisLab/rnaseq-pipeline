#!/bin/bash

export MODES=$2 # Need to do this before in case MODES has something important (e.g. $SCHEDULER_PORT)
set -eu
echo "Loading config for $0 from $PWD using MODES: $MODES"
source ../etc/load_configs.sh
echo "Config loaded."

if [ $# -lt 3 ]
  then
    GSE="GSE64978"
    JOB="ProcessGSE"
    MODES="mouse,distributed"
    echo "Incorrect arguments."
    echo "Example:"
    echo "  $0 $JOB $MODES --gse=$GSE [other args]"
    exit -1
fi

JOB=$1
# Pop non-pipeline arguments
shift 
shift 

echo "Scheduling $JOB job for $@"

## Export environment variables that tasks/subtasks will need.
export MODES=$MODES
export DATA=$DATA
export QUANTDIR=$QUANTDIR
export RESULTS_DIR=$RESULTS_DIR
export TMPDIR=$TMPDIR
export COUNTDIR=$COUNTDIR
export SCRIPTS=$SCRIPTS
export METADATA=$METADATA
export GEMMACLI=$GEMMACLI
export GEMMA_LIB=$GEMMA_LIB
export JAVA_OPTS="-Dgemma.log.dir=$HOME/gemmalogs -Dehcache.disk.sort.dir=$HOME/gemmacache -Xmx45g -XX:MaxPermSize=256M" # TODO: Make part of configs?

echo @ $@
# Assuming the --gse argument is required.
export CURRENTGSE=$(echo $@ \
    | tr " " "\n" \
    | grep "\-\-gse\=" \
    | sed 's|\-\-gse\=||g' \
    | head -n1)

echo "Current GSE="$CURRENTGSE
echo "Args=" $@
MODES=$MODES PYTHONPATH='.' luigi --scheduler-port $SCHEDULER_PORT $SCHEDULER_HOST --module tasks $JOB $@
