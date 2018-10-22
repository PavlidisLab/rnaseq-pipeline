#!/bin/bash
## Convert .bam files to .fastq
set -eu
source ../etc/load_configs.sh

REQUIRED_NARGS=3
MAX_NARGS=4
if [ "$#" -lt $REQUIRED_NARGS ] || [ "$#" -gt $MAX_NARGS ]; then
    echo " Usage:"
    echo "$0" "SERIES" "REGEX" "OUTPUT <Optional, --paired-end>"
    echo " Example for bam regex: '*.bam'"
    exit
fi

SERIES=$1
REGEX=$2
OUTPUT=$3

PARALLEL_MACHINES=""
if [ -n "$MACHINES" ]; then
    echo "Using distributed mode on: $MACHINES"
    PARALLEL_MACHINES=" -S $MACHINES "
fi

export BAMTOFASTQ="/space/grp/bin/bamToFastqUnsorted" # TODO: Make this more seamless (use the -i -bam like in the bedtool script.)
if [ "$#" -gt $REQUIRED_NARGS ]; then
    # Paired-end
    find $DATA/$SERIES -name "$REGEX" \
	| parallel $PARALLEL_MACHINES -P $NCPU_NICE --workdir $(dirname {1}) $BAMTOFASTQ {1} $(basename {1})"_1.fastq" $(basename {1})"_2.fastq"
    #| parallel $PARALLEL_MACHINES -P $NCPU_NICE --workdir $(dirname {1}) $BAMTOFASTQ "-i" <(samtools sort -n {1}) "-fq "$(basename {1})"_1.fastq" "-fq2 "$(basename {1})"_2.fastq"
else
    # Paired-end
    find $DATA/$SERIES -name "$REGEX" #\
	#| parallel $PARALLEL_MACHINES -P $NCPU_NICE --workdir $(dirname {1}) $BAMTOFASTQ "-i" <(samtools sort -n {1}) "-fq "$(basename {1})".fastq" >/dev/null 2>&1
fi
