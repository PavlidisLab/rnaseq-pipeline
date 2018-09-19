#!/bin/bash
source ../etc/load_configs.sh
set -eu

echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo "! DO NOT USE UNTIL REVIEWED. THIS SCRIPT IS NOT MAINTAINED. !"
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

if [ "$#" -ne 1 ]; then
    ACCESSION="GSE12345"
    echo "Description: "
    echo "Run seqpurge on all files in a project."
    echo "Usage:"
    echo "$0 <ACCESSION>"
    echo "Example:"
    echo "$0 $ACCESSION"
    echo "   where $TMPDIR/$ACCESSION would hold all the temporary data."
    exit -1
fi
PROJECTDIR=$1
exit -1

export TRIMMED_DIR=/cosmos/data/pipeline-output/rnaseq/data/$PROJECTDIR

find /cosmos/data/pipeline-output/rnaseq/data/$PROJECTDIR/ \
    | rev \
    | cut -f1 -d"/" --complement \
    | rev \
    | grep PEC \
    | sort | uniq \
    | xargs -I@ ./samplist-DIRTY.sh @ BrainGVEX \
    | parallel -P10 -X --colsep ' ' $SCRIPTS/purge_fastq.sh {1} {2} BrainGVEX
