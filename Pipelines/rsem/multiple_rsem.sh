#!/bin/bash

FILES=$1
NPROC=$(grep -c ^processor /proc/cpuinfo)
NPROC=2 # Set to 2 because limited memory.

echo "Launching parallel RSEM."
find $FILES/ -name "*.fastq.gz" | parallel -P $NPROC -I @ ./rsem_fix.sh @ @