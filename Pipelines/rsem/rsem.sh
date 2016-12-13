#!/bin/bash
set -eu
source ../../etc/load_configs.sh

if [ $# -eq 0 ]
    then
    SERIES="GSE123456"
    OUTPUT="quantified/$SERIES/SAMPLE1.fasrq.gz"
    echo "Usage:"
    echo $0" $SERIES SAMPLE1.fastq.gz <Optional, SAMPLE2.fastq.gz>"    
    exit
fi

RSEM_EXE="$RSEM_DIR/rsem-calculate-expression"
REFERENCE=$STAR_DEFAULT_REFERENCE
REFERENCE="/misc/pipeline42/NeuroGem/pipeline/runtime/mouse_ref38/mouse_0" 

SERIES=$1
SAMPLE=$(basename $2)

OUTPUT="quantified/$SERIES/$SAMPLE"
TMP="temporary/$SERIES/$SAMPLE"


mkdir -p $OUTPUT
mkdir -p $TMP

if [ $# -eq 0 ]
    then
    echo "No arguments supplied. Please specify one or two (for paired-end data) fastq file(s)."
    exit
fi

PAIRED_END=""
PAIR=""

CMD=$(echo $RSEM_EXE \
    -p 1 \
    --star-gzipped-read-file \
    --temporary-folder $TMP \
    --time \
    --star \
    --star-path $STAR_PATH \
    "$2" \
    $OUTPUT \
    $REFERENCE \
    "--star-shared-memory LoadAndKeep" 
)

if [ $# -gt 2 ]
    then
    PAIRED_END=" --paired-end "
    PAIR=$3

    ## For some reason, the order of the parameters change for paired-end data.
    CMD=$(echo $RSEM_EXE \
    -p 1 \
    --star-gzipped-read-file \
    --temporary-folder $TMP \
    --time \
    --star \
    --star-path $STAR_PATH \
    "$2 $PAIR" \
    $REFERENCE \
    $OUTPUT \
    "--star-shared-memory LoadAndKeep" \
    $PAIRED_END
)
fi

echo $CMD
$CMD