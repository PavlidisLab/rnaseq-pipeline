#!/bin/bash
set -eu
##	SYNOPSIS:
##		purge_fastq.sh <Mate1> <optional:Mate2> <ProjectID>
##
##	AUTHOR: 
##		Manuel Belmadani
##
##	DESCRIPTION: 
##		Purge adapter content from fastq files.
##	
##


source ../etc/load_configs.sh

FASTQ_A=$1
if [ $# -gt 2 ]; then
    FASTQ_B=$2
    
    PROJECT=$3
    OUT_B=$(echo $FASTQ_B | sed "s|$PROJECT|$PROJECT-TRIMMED|g")  
else
    FASTQ_B=""
    OUT_B=""
    PROJECT=$2
fi

OUT_A=$(echo $FASTQ_A | sed "s|$PROJECT|$PROJECT-TRIMMED|g" )

#$TRIMMED_DIR/$PROJECT/$(basename $FASTQ_A)
#OUT_B=$TRIMMED_DIR/$PROJECT/$(basename $FASTQ_B)

mkdir -p $(dirname $OUT_A)
mkdir -p $(dirname $OUT_B)

## Execute SeqPurge
$SEQPURGE -in1 $FASTQ_A -in2 $FASTQ_B -out1 $OUT_A -out2 $OUT_B
