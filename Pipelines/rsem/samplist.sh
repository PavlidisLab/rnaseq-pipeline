#!/bin/bash
set -eu

source ../../etc/load_configs.sh &> /dev/null # Be quiet!

if [ $# -eq 0 ]
    then
    echo "Usage:"
    echo $0" PATH_TO_SAMPLE_RUNS <Optional, --paired-end>"    
    echo "Description:"
    echo "For a path with multiple sequencing runs, assemble the list of sequences and mates if --paired-end is provided."
    exit
fi

include_exclude () 
{

    if [ -z ${EXCLUDEME+x} ] && [ -z ${INCLUDEME+x} ]; then
	# Case where no Include/Exclude filters are used
	INPUTS="$1"
	return 0
    fi

    # Sets FILES globally depending on what the include/exclude files requested.
    INPUTS=""

    #EXCLUDESTR=$(cat $EXCLUDEME | tr '\n' '|' | sed 's/|$//g')

    for sample in $(echo $1 | tr ',', '\n'); do
	INPUT=""
	if [ ! -z ${EXCLUDEME+x} ] && [ -f $EXCLUDEME ]; then
	    # Remove files in EXCLUDEME
	    #INPUT=$(echo $sample | egrep -v "($EXCLUDESTR)" || : )
	    INPUT=$(echo $sample | egrep -v -f $EXCLUDEME || : )
	fi

	if [ ! -z ${INCLUDEME+x} ] && [ -f $INCLUDEME ]; then
	    # Retain only INCLUDEME if specified.
	    INPUT=$(echo $sample | grep -f $INCLUDEME || : )
	fi
	
	if [ ! "$INPUT" == "" ]; then
	    INPUTS="$INPUTS""$INPUT"","
	fi
    done
    return 0
}

BEFORE=$DEFAULT_MATE_SOURCE
AFTER=$DEFAULT_MATE_REPLACEMENT

INPUTS=$(find $1"/" -name "*.fastq.gz"| tr "\n" "," | tr " " ",")
include_exclude $INPUTS # Call inclusion/exclusion subroutine

FILES=$(echo $INPUTS | sed 's/,$//g' )

MATES=""

if [ $# -eq 2 ]
then
    if [ $2 = "--paired-end" ]
    then
	INPUTS=$(find $1"/" -name "*$BEFORE*.fastq.gz" | tr "\n" "," | tr " ", "," )
	include_exclude $INPUTS # Call inclusion/exclusion subroutine
	FILES=$(echo $INPUTS| sed 's/,$//g')
	MATES=$(echo $FILES | sed "s/$BEFORE/$AFTER/g")
    else
	echo "Unknown parameter: $2"
	exit
    fi
fi

if [ ! -z $FILES ]; then
    echo $FILES $MATES
fi
