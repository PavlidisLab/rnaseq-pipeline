#!/bin/bash
## Rescue FASTQ files from BAM.

set -eu
source ../../etc/load_configs.sh

REQUIRED_NARGS=3

if [ $# -lt $REQUIRED_NARGS ]; then
    echo " Usage:"
    echo "$0" "InputDirectory/" "BamRegex" "OutputDirectory/ <Optional, --paired-end>"
    echo " Example for bam regex: '*.bam'"
    exit
fi

INPUT=$1
REGEX=$2
OUTPUT=$3
PAIRED=$4

find "$INPUT" -name "$BamRegex" | \
    parallel $PARALLEL_MACHINES -P $NCPU_NICE  $PICARD $SERIES {1} {2} >> resq-log.txt

