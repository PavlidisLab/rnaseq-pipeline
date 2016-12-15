#!/bin/bash
set -eu
source ../../etc/load_configs.sh

if [ $# -eq 0 ]
    then
    SERIES="GSE123456"
    OUTPUT="quantified/$SERIES/SAMPLE1.fastq.gz"
    echo "Usage:"
    echo $0" $SERIES SAMPLE1.fastq.gz <Optional, SAMPLE2.fastq.gz>"    
    exit
fi

RSEM_EXE="$RSEM_DIR/rsem-calculate-expression"
REFERENCE=$STAR_DEFAULT_REFERENCE
REFERENCE="/misc/pipeline42/NeuroGem/pipeline/runtime/mouse_ref38/mouse_0" 

SERIES=$1
SAMPLE=$(echo $(basename $2) | sed 's/.fastq.gz//g')

OUTPUT="quantified/$SERIES/$SAMPLE"
TMP="temporary/$SERIES/$SAMPLE"

mkdir -p $OUTPUT
mkdir -p $TMP

SEQUENCES=$2
PAIRED_END=""
MATE=""


if [ $# -gt 3 ] 
then
    PAIRED_END=" --paired-end "
    MATES=$3

    CMD=$(echo $RSEM_EXE \
	-p 8 \
	--star-gzipped-read-file \
	--temporary-folder $TMP \
	--time \
	--star \
	--star-path $STAR_PATH \
	$PAIRED_END \
	" $SEQUENCES $MATE " \
	$REFERENCE \
	$OUTPUT \
	"--star-shared-memory LoadAndKeep" \
)
else
    CMD=$(echo $RSEM_EXE \
	-p 8 \
	--star-gzipped-read-file \
	--time \
	--star \
	--star-path $STAR_PATH \
	--temporary-folder $TMP \
	" $SEQUENCES " \
	$REFERENCE \
	$OUTPUT \
	"--star-shared-memory LoadAndKeep"
    )   
fi

echo $CMD >> log.txt
$CMD