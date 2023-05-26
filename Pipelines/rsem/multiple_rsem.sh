#!/bin/bash
set -eu
source ../../etc/load_configs.sh

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
    if [ $3 == "--paired-end" ] || [ $3 == "--mixed" ] ||
	[ $3 == "--paired-end-only" ]
    then
	MATES="$3"
    else
	echo "Error: Arg 3 should be --paired-end, --paired-end-only or --mixed."
	exit -1
    fi
else
    if [ $# -gt 3 ]
    then
	echo "Too many arguments! Please check your command."
	exit -1
    fi
fi

FILES=$1
SERIES=$2
REFERENCE=$(dirname $STAR_DEFAULT_REFERENCE)
PARALLEL_MACHINES=""
if [ -n "$MACHINES" ]; then
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

#echo "Preparing memory..."
#$RSEM_DIR/rsem-star-load-shmem $STAR_EXE $REFERENCE $NCPU
#echo "Memory loaded."

echo "Launching parallel RSEM for:"
#echo "Template:"  "$SEM --wait --colsep ' ' -n2 -P $NCPU ./rsem.sh $SERIES {1} {2}"
find $FILES/ -name "*.fastq.gz" -exec dirname {} \; | sort | uniq |  # Get samples directories, sorted and unique.
    xargs -n1 -I % ./samplist.sh % $MATES | # Prepare sample pairs.    
    parallel $PARALLEL_MACHINES -P $NCPU_NICE --jobs $NCPU_NICE --colsep ' ' $(pwd)/rsem.sh $SERIES {1} {2} >> parallel-log.txt
    
#echo "Flushing memory..."
#echo "Skipped!"
#$RSEM_DIR/rsem-star-clear-shmem $STAR_EXE $REFERENCE $NCPU
#echo "Memory flushed."

echo "Done."
