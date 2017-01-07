#!/bin/bash
set -eu
source ../../etc/load_configs.sh &> /dev/null # Be quiet!

if [ $# -eq 0 ]
    then
    echo "Usage:"
    echo $0" PATH_TO_SAMPLE_RUNS <Optional, --paired-end>"    
    echo "Description:"
    echo "For a path with multiple sequencing runs, assemble the list of sequences and mates (if --paired-end is provided"
    exit
fi

BEFORE=$DEFAULT_MATE_SOURCE
AFTER=$DEFAULT_MATE_REPLACEMENT

FILES=$(find $1"/" -name "*.fastq.gz" | tr "\n" "," | sed 's/,$//g' )
MATES=""

if [ $# -eq 2 ]
then
    if [ $2 = "--paired-end" ]
    then	
	FILES=$(find $1"/" -name "*$BEFORE*.fastq.gz" | tr "\n" "," | sed 's/,$//g' )	
	MATES=$(echo $FILES | sed "s/$BEFORE/$AFTER/g")
    else
	echo "Unknown parameter: $2"
	exit
    fi
fi

echo $FILES $MATES
