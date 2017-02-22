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
    echo " Using paired-end sequences. "
    MATES=" --paired-end "
else
    if [ $# -gt 3 ]
    then
	echo "Too many arguments! Please check your command."
	exit -1
    fi
    echo " Using single-end sequences. "
fi

FILES=$1
SERIES=$2
REFERENCE=$(dirname $STAR_DEFAULT_REFERENCE)

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

echo "Launching parallel Stringtie for:" $FILES

find $FILES/ -name "*.fastq.gz" -exec dirname {} \; | # Get samples directories 
    sort | # sorted
    uniq | # and unique.
    xargs -n1 -I % ./samplist.sh % $MATES | # Prepare sample (in pairs if needed).
    parallel -S rod,todd -P 0 --colsep ' ' $(pwd)/stringtie.sh $SERIES {1} {2} >> parallel-log.txt
    
#echo "Flushing memory..."
#$RSEM_DIR/rsem-star-clear-shmem $STAR_EXE $REFERENCE $NCPU
#echo "Memory flushed."

echo "Done."