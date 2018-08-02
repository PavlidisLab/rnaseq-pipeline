#!/bin/bash

set -eu
source ../../etc/load_configs.sh

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
    echo "   Note: If --paired-end is not specified, then automatic detection will be performed."
    echo "Example:"
    echo "$0 $FILES $SERIES"
    echo "   where $FILES would have each sample under it's own directory."
    exit -1
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

export MODES=$MODES  # TODO: Doesn't seem needed.
echo "$0 using modes: $MODES"

FILES=$1
SERIES=$2
SAMPLIST="$ROOT_DIR/Pipelines/rsem/samplist.sh" # TODO: Centralize into scripts/ directory.

# Save excution metadata
## Assuming $configfile from etc/load_configs.sh is set.
CONFIGDIR=$METADATA"/"$SERIES"/configurations/"
mkdir -p $CONFIGDIR
configfileDest="multiple_rsem_"$(basename $configfile)
cp $configfile $CONFIGDIR/$configfileDest
##

CURRENTLOGDIR=$LOGS/$SERIES
if [ $CLEARLOGS == "1" ]; then
	find $CURRENTLOGDIR -name "*.log" -delete
	find $CURRENTLOGDIR -name "*.err" -delete
fi

# CURRENTLOGS is a prefix
CURRENTLOGS=$CURRENTLOGDIR/$(basename $0)
mkdir -p $CURRENTLOGDIR # Initialize log directory


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
    FILES=$DATA"/"$FILES"/"
    echo "Searching for files in $DATA."
    if [[ -d $FILES ]]; then
	echo "Using files at path $FILES"
    else
	echo "No files found at $1 or $FILES."
	echo "Abort."
	exit 1
    fi
fi

echo "Preparing memory..."
# echo $MACHINES | tr ',' '\n' | parallel -n0 $PARALLEL_MACHINES $RSEM_DIR/rsem-star-load-shmem $STAR_EXE $REFERENCE_DIR $NCPU_NICE
echo "Memory loaded."


# If directories exists, clean them.
#quantDir=$(pwd)"/quantified/$SERIES" # TODO: This should be part of config variables
#tmpDir=$(pwd)"/temporary/$SERIES" # TODO: This should be part of config variables

quantDir="$QUANTDIR/$SERIES" 
tmpDir="$TMPDIR/$SERIES" 

printf  "Reprocess is set to $REPROCESS."
if [ $REPROCESS == "1" ]; then
    cleanQuant="rm -rf $quantDir"
    cleanTmp="rm -rf $tmpDir"

    if [ -d $quantDir ]; then
	echo "Cleaning stale quantification data at $quantDir"
	echo $cleanQuant
	$cleanQuant
    fi

    if [ -d $tmpDir ]; then
	echo "Cleaning stale temporary data at $tmpDir"
	echo $cleanTmp
	$cleanTmp
    fi
else
    echo " Nothing to do/Not deleting files before processing."
fi

echo "Launching RSEM for: $SERIES"
# Get samples directories, sorted and unique.
# Prepare sample pairs.    
# Run in parallel
# samplist.sh will return the sequence (and mates) as 1 (or 2) lists of FASTQ files.
find -L $FILES/ -name "*.fastq*" -exec dirname {} \; \
    | sort \
    | uniq \
    | xargs -n1 -I % $SAMPLIST % $MODES $MATES \
    | parallel --env MODES $PARALLEL_MACHINES  -j $NJOBS --colsep ' '  $(pwd)/rsem.sh $SERIES {1} {2} > $CURRENTLOGS.log 2> $CURRENTLOGS.err

echo "Flushing shared memory temporarily disabled; don't forget to clear your mempry once you're done!"

#echo "Flushing memory..."
#echo $MACHINES | tr ',' '\n' | parallel -S $MACHINES $RSEM_DIR/rsem-star-clear-shmem $STAR_EXE $REFERENCE_DIR $NCPU_NICE
#$RSEM_DIR/rsem-star-clear-shmem $STAR_EXE $REFERENCE_DIR $NCPU_NICE

# echo "Memory flushed."

# echo "Done calling RSEM."
# if [ -d $tmpDir ]; then
#     echo "Cleaning stale temporary data at $quantDir"
#     echo $cleanTmp
#     $cleanTmp
# fi
