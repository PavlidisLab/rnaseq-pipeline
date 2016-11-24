#!/bin/bash

RSEM_EXE="/misc/pipeline42/NeuroGem/pipeline/RSEM/bin/rsem-calculate-expression"
STAR="/space/bin/STAR-STAR_2.4.0h/bin/Linux_x86_64_static"
#REFERENCE="/misc/pipeline42/NeuroGem/pipeline/runtime/human_ref38/human_0"
REFERENCE="/misc/pipeline42/NeuroGem/pipeline/runtime/mouse_ref38/mouse_0"

SAMPLE=$(basename $1)
OUTPUT="quantified/$SAMPLE"
TMP="temporary/$SAMPLE"


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
    -p 16 \
    --temporary-folder $TMP \
    --time \
    --star \
    --star-path $STAR \
    <(zcat -f $@) \
    $REFERENCE \
    $OUTPUT   