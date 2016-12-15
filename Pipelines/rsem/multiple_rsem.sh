#!/bin/bash
set -eu
source ../../etc/load_configs.sh

if [ $# -eq 0 ]
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
    MATES=1
else
    if [ $# -gt 3 ]
	echo "Too many arguments! Please check your command."
	exit -1
    fi
fi

FILES=$1
SERIES=$2
REFERENCE=$(dirname $STAR_DEFAULT_REFERENCE)
NCPU=1 # Set to 2 because limited memory.

echo "Preparing memory..."
$RSEM_DIR/rsem-star-load-shmem $STAR_EXE $REFERENCE $NCPU #/misc/pipeline42/NeuroGem/pipeline/runtime/human_ref38/
echo "Memory loaded."

echo "Launching parallel RSEM."

find $FILES/ -name "*.fastq.gz" | parallel -P $NCPU --load "$MAX_CPU_LOAD" -I % ./rsem.sh $SERIES %

echo "Flushing memory..."
$RSEM_DIR/rsem-star-clear-shmem $STAR_DIRECTORY $REFERENCE $NCPU
echo "Memory flushed."