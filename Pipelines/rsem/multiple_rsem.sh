#!/bin/bash

set -eu
source ../../etc/load_configs.sh
mkdir -p $LOGS/$(basename $0)

echo "USING MACHINES: $MACHINES"

if [ $# -lt 2 ]
    then
    FILES="data/GSE123456/"
    SERIES="GSE123456"
    echo "Description: "
    echo "Provide a directory where sample runs are contained by distinct directories."
    echo "Usage:"
    echo "$0 <FILES> <SERIES>"
    echo "$0 <FILES> <SERIES> --paired-end"
    echo "Example:"
    echo "$0 $FILES $SERIES"
    echo "   where $FILES would have each sample under it's own directory."
    exit
fi

MATES=""
if [ $# -eq 3 ]
then
    MATES=" --paired-end "
    echo "Setting to --paired-end"
else
    if [ $# -gt 3 ]
    then
	echo "Too many arguments! Please check your command."
	exit -1
    fi   
fi

FILES=$1
SERIES=$2
SAMPLIST="/space/grp/Pipelines/rnaseq-pipeline/Pipelines/rsem/samplist.sh"
REFERENCE_DIR=$(dirname $STAR_DEFAULT_REFERENCE)
PARALLEL_MACHINES=""
if [ -n "$MACHINES" ]; then
    echo "Using distributed mode on: $MACHINES"
    PARALLEL_MACHINES=" -S $MACHINES "
fi

if [[ -d $FILES ]]; then
    # Path is a directory, no need to preprend $DATA directory.
    echo "Using files at path $FILES"
else
    # Look for files in $DATA.
    FILES=$DATA"/"$FILES
    echo "Searching for files in $DATA."
    if [[ -d $FILES ]]; then
	echo "Using files at path $FILES"
    else
	echo "No files found at $1 or $FILES."
	echo "Abort."
	exit 1
    fi
fi

if [ "$MATES" == "" ]; then
    isMate=$(find $FILES | grep -c "$DEFAULT_MATE_REPLACEMENT") || :
    echo "Found $isMate potential mates."
    if [ $isMate -gt 0 ];
    then  
	echo "Automatically detected --paired-end sequences."
	MATES="--paired-end"
    else
	echo "No mate-pairs found. Treating as single-end sequences."
    fi    
fi

echo "Preparing memory..."
# echo $MACHINES | tr ',' '\n' | parallel -n0 $PARALLEL_MACHINES $RSEM_DIR/rsem-star-load-shmem $STAR_EXE $REFERENCE_DIR $NCPU_NICE
echo "Memory loaded."


# If directories exists, clean them.
quantDir=$(pwd)"/quantified/$SERIES" # TODO: This should be part of config variables
tmpDir=$(pwd)"/temporary/$SERIES" # TODO: This should be part of config variables

cleanQuant="rm -rf $quantDir"
cleanTmp="rm -rf $tmpDir"

if [ -d $quantDir ]; then
    echo "Cleaning stale quantification data"
    echo $cleanQuant
    $cleanQuant
fi

if [ -d $tmpDir ]; then
    echo "Cleaning stale temporary data"
    echo $cleanTmp
    $cleanTmp
fi

echo "Launching RSEM for: $SERIES"
# Get samples directories, sorted and unique.
# Prepare sample pairs.    
# Run in parallel
find $FILES/ -name "*.fastq.gz" -exec dirname {} \; \
    | sort \
    | uniq \
    | xargs -n1 -I % $SAMPLIST % $MATES \
    | parallel --env MODES $PARALLEL_MACHINES -P $NCPU_NICE --jobs $NCPU_NICE --colsep ' '  $(pwd)/rsem.sh $SERIES {1} {2} >> $LOGS/$(basename $0)/$SERIES.log 2>> $LOGS/$(basename $0)/$SERIES.err

echo "Flushing memory..."
# echo $MACHINES | tr ',' '\n' | parallel -n0 $RSEM_DIR/rsem-star-clear-shmem $STAR_EXE $REFERENCE_DIR $NCPU_NICE
echo "Memory flushed."

echo "Done."
