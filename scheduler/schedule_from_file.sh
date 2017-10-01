#!/bin/bash

source ../etc/load_configs.sh
set -eu

if [ "$#" -lt 2 ]; then
    echo "Usage:"
    echo " $0 FILE JOB"
    echo 
    echo "File should have format: EEID GSE TAXON NSAMPLES"
    echo
    echo "Example:"
    echo -e "eeID\teeName\ttaxon\tsample"
    echo -e "-1\tGSE64978\trat\t10"
    exit -1
fi

# TODO: 
GEO_SAMPLES="$1"
JOB="$2"

OUTPUT="$LOGS/MultiScheduler/"$(basename $GEO_SAMPLES)
echo "Writing logs in $OUTPUT"
mkdir -p $(dirname $OUTPUT)

echo "##================Launching new batch======================##"
sed 's|\t| |g' $GEO_SAMPLES \
    | cut -d' ' -f2,3,4 \
    | tail -n +2 \
    | grep -v "^$" \
    | parallel --jobs $NTASKS \
               --colsep " " \
               --progress \
                ./schedule.sh "$JOB {2},distributed --gse {1} --nsamples {3}"  #1>> $OUTPUT".out" 2>> $OUTPUT".err"
