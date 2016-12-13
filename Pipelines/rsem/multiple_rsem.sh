#!/bin/bash
set -eu
source ../../etc/load_configs.sh

FILES=$1
SERIES=$2
REFERENCE=$(dirname $STAR_DEFAULT_REFERENCE)
#NCPU=3 # Set to 2 because limited memory.

echo "Preparing memory..."
$RSEM_DIR/rsem-star-load-shmem $STAR_EXE $REFERENCE $NCPU #/misc/pipeline42/NeuroGem/pipeline/runtime/human_ref38/
echo "Memory loaded."

echo "Launching parallel RSEM."

find $FILES/ -name "*.fastq.gz" | parallel -P $NCPU --load "$MAX_CPU_LOAD" -I % ./rsem.sh $SERIES %

echo "Flushing memory..."
$RSEM_DIR/rsem-star-clear-shmem $STAR_DIRECTORY $REFERENCE $NCPU
echo "Memory flushed."