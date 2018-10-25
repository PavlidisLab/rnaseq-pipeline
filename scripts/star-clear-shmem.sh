#!/bin/bash
set -eu

if [ "$#" -gt 1 ] || ( [ "$#" -eq 1 ] && ( [ "$1" == "-h" ] || [ "$1" == "--help" ] ) ) ; then
    MODES="distributed"
    echo "Description: "
    echo "Clear all shared memory on required servers."
    echo "Usage:"
    echo "$0 <MODES, options>"
    echo "If MODES is not given, then the MODES environment variable will be used."
    echo "Example:"
    echo "$0 $MODES"
    exit -1
fi

if [ "$#" -eq 1 ]; then
    export MODES=$1
    echo "MODES set to $MODES"
fi
source ../etc/load_configs.sh &> /dev/null

echo "MACHINES: $MACHINES"
PARALLEL_MACHINES=""
NJOBS=1
if [ -n "$MACHINES" ]; then
    echo "Using distributed mode on: $MACHINES"
    NJOBS=$(echo $MACHINES | tr "," "\n" | wc -l)
    PARALLEL_MACHINES=" -S $MACHINES "
fi

seq $NJOBS \
    | parallel -n0 \
    $PARALLEL_MACHINES \
    --progress \
    --workdir $SCRIPTS \
    ./clearAllMem.sh

