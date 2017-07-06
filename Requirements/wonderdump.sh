#!/bin/bash

#
# Wonderdump is a workaround to download SRA files directly
# when fastq-dump internet connection does not work. For example on Bash on Windows.
#
# Usage:
#   wonderdump SRR1553500 -X 10000

set -ue

# cd $(dirname $0) 
source ../etc/load_configs.sh

# ASSUMING CONFIGURATION FILE HAS $FASTQDUMP_EXE

# The first paramter must be the SRR number.
SRR=$1

# This is where we will store the file.
SRA_DIR=$2

# Make the directory if it does not exist.
mkdir -p $SRA_DIR

# Create the full path to the file.
SRA_FILE="$SRA_DIR/$SRR.sra"
TMP_FILE="$SRA_DIR/$SRR.tmp"

# Download only if it does not exist.
if [ ! -f $SRA_FILE ];
then
    PATH1=${SRR:0:6}
    PATH2=${SRR:0:10}
    echo "*** downloading: $SRA_FILE"
    curl ftp://ftp-trace.ncbi.nih.gov/sra/sra-instant/reads/ByRun/sra/SRR/${PATH1}/${PATH2}/${SRR}.sra > $TMP_FILE
    mv $TMP_FILE $SRA_FILE
fi

# Shift paramters
shift

# Are there parameters left.
if [ $# -gt 0 ]
then
    # Run the fastq-dump.
    CMD="$FASTQDUMP_EXE $SRA_FILE --outdir $SRA_DIR --gzip --skip-technical  --readids --dumpbase --split-files --clip"
    $CMD
    #$FASTQDUMP_EXE ${SRA_FILE}
fi
