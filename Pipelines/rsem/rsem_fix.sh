#!/bin/bash
set -eu
source ../../etc/load_configs.sh

RSEM_EXE="$RSEM_DIR/rsem-calculate-expression"
STAR="/space/bin/STAR-STAR_2.4.0h/bin/Linux_x86_64_static"
REFERENCE="/misc/pipeline42/NeuroGem/pipeline/runtime/human_ref38/human_0"

SAMPLE=$(basename $1)
SERIES=$2 # TODO : Make this nicer

OUTPUT="quantified/$2/$SAMPLE"
TMP="temporary/$2/$SAMPLE"


mkdir -p $OUTPUT
mkdir -p $TMP

if [ $# -eq 0 ]
    then
    echo "No arguments supplied. Please specify one or two (for paired-end data) fastq file(s)."
    exit
fi

if [ $# -gt 0 ]
    then
    ARGUMENTS="<(zcat -f $1)"
fi

if [ $# -eq 0 ]
    then
    echo "Paired-end version not implemented."
    exit
fi

#    <(zcat -f $@) \
#    <(zcat -f $1) <(zcat -f /dev/null) \
#    --paired-end \
$RSEM_EXE \
    -p 1 \
    --temporary-folder $TMP \
    --time \
    --star \
    --star-path $STAR \
    <(zcat -f $@) \
    $REFERENCE \
    $OUTPUT   