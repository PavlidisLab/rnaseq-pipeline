#!/bin/bash

source ../etc/load_configs.sh
set -eu

##
## !!! This is a modified version of the script to do per-machine scheduling right at this level.
## The method is pretty flimsy and might break if we change the tasks in the scheduler.

if [ "$#" -lt 2 ]; then
    echo "Usage:"
    echo " $0 FILE JOB"
    echo "MODES=centos5,distributed $0 FILE JOB"
    echo 
    echo "File should have format: EEID GSE TAXON NSAMPLES"
    echo "The MODES= environment variable will add additional modes from etc/modes."
    echo
    echo "Example:"
    echo -e "eeID\teeName\ttaxon\tsample"
    echo -e "-1\tGSE64978\trat\t10"
    exit -1
fi

PARALLEL_MACHINES=""
if [ -n "$MACHINES" ]; then
    echo "Using distributed mode on: $MACHINES"
    PARALLEL_MACHINES=" -S $MACHINES "
fi

# TODO: 
GEO_SAMPLES="$1"
JOB="$2"
if [ -z ${MODES+x} ]; then 
    echo "MODES is unset"; 
    MODES=""
else 
    echo "MODES is set to '$MODES'"; 
    MODES=$MODES","
fi

OUTPUT="$LOGS/MultiScheduler/"$(basename $GEO_SAMPLES)
echo "Writing logs in $OUTPUT"
mkdir -p $(dirname $OUTPUT)

GEMMAINFO=" --env GEMMAUSERNAME --env GEMMAPASSWORD --env GEMMACLI "

echo "##================Launching new batch======================##"
echo " Rate: $NTASKS tasks simultaneously. " 
sed 's|\t| |g' $GEO_SAMPLES \
    | cut -d' ' -f2,3,4 \
    | tail -n +2 \
    | grep -v "^$" \
    | grep -f <($ROOT_DIR/scheduler/progressReport.sh | grep -P "X\tX\tX\tX\tX\t[_X]\t_" | cut -f1) \
    | parallel \
        $PARALLEL_MACHINES \
        $GEMMAINFO \
        --jobs $NTASKS \
        --colsep " " \
        --progress \
        --workdir $PWD \
        $PWD/schedule.sh "$JOB $MODES{2} --gse={1} --nsamples={3}" 

# Removed from the pipe:     | grep -f <($ROOT_DIR/scheduler/progressReport.sh | grep -P "X\tX\tX\tX\tX\t[_X]\t_" | cut -f1) \ 
