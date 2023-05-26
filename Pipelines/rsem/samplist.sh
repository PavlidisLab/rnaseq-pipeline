#!/bin/bash
set -eu
source ../../etc/load_configs.sh &> /dev/null # Be quiet!

if [ $# -eq 0 ]
    then
    echo "Usage:"
    echo $0" PATH_TO_SAMPLE_RUNS <Optional, --paired-end>"    
    echo "Description:"
    echo "For a path with multiple sequencing runs, assemble the list of sequences and mates (if --paired-end is provided"
    exit -1
fi

BEFORE=$DEFAULT_MATE_SOURCE
AFTER=$DEFAULT_MATE_REPLACEMENT

FILES=$(find $1"/" -name "*$BEFORE*.fastq.gz" | tr "\n" "," | sed 's/,$//g' )
MATES="/inexistant/path"

# Check for file existance
find $1"/" -name "*$BEFORE*.fastq.gz" -exec stat {} \; > /dev/null

if [ $# -eq 2 ]
then
    # Check for mate existance
    find $1"/" -name "*$AFTER*.fastq.gz" -exec stat {} \;  > /dev/null

    FILES=$(find $1"/" -name "*$BEFORE*.fastq.gz" | tr "\n" "," | sed 's/,$//g' ) # First root pair
    MATES=$(echo $FILES | sed "s/$BEFORE/$AFTER/g")  # Path for mates, check later if they exist

    if [ $2 = "--paired-end" ]
    then	
	if [ ! -f $(echo $MATES | cut -f1 -d"," ) ]; then
	    echo "File not found! Use --paired-end-only to only process paired end files or no parameter to do either case-by-case."
	    echo $MATES
	    exit -1
	fi	
    elif [ $2 = "--paired-end-only" ]
    then
	FIRSTMATE=$(echo $MATES | cut -f1 -d"," )
	#echo "Check: >>> $FIRSTMATE  <<<" 
	if [ ! -f $FIRSTMATE ]; then	    
	    exit 0 # Exit without printing anything.	    
	fi	

    elif [ $2 = "--mixed" ]
    then
	FIRSTMATE=$(echo $MATES | cut -f1 -d"," )
	#echo "Check: >>> $FIRSTMATE  <<<" 
	if [ ! -f $FIRSTMATE ]; then	    
	    # Clear MATES since 
	    MATES=""
	fi	
	#echo "wiped: >>> $MATES  <<<" 
    else
	echo "Unknown parameter: $2"
	exit -1
    fi
else
    MATES=""
fi


if [ ! -z $FILES ]; then
    echo $FILES $MATES
fi
