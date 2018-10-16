#!/bin/bash
set -eu

cd $(dirname $0) 
source ../etc/load_configs.sh

if [ "$#" -ne 1 ]; then
    ACCESSION="E-MTAB-4092"
    echo "Description: "
    echo "Provide an ArrayExpress identifier to download all fastq files from.."
    echo "Usage:"
    echo "$0 <ACCESSION>"
    echo "Example:"
    echo "$0 $ACCESSION"
    echo "   where $DATA/$ACCESSION would hold all the downloaded data."
    exit -1
fi

# Set up arguments
AE_ID="$1"
OUTPUT_PATH=$DATA"/"$AE_ID
mkdir -p $OUTPUT_PATH

# Set up logs
LOGDIR=$LOGS/$(basename $0)
LOGFILES=$LOGDIR/$AE_ID
mkdir -p $LOGDIR


FILENAME=$AE_ID".sdrf.txt"
SAMPLE_MATRIX_URL="http://www.ebi.ac.uk/arrayexpress/files/"$AE_ID"/"$FILENAME

SAMPLE_MATRIX="/tmp/"$FILENAME
wget -P /tmp "$SAMPLE_MATRIX_URL"

FASTQ_HEADER="Comment[FASTQ_URI]"
SAMPLE_HEADER="Comment[ENA_RUN]"

FASTQ_INDEX=$(head -n1 /tmp/$FILENAME | tr "\t" "\n" | fgrep -n "$FASTQ_HEADER" | cut -f1 -d":")
SAMPLE_INDEX=$(head -n1 /tmp/$FILENAME | tr "\t" "\n" | fgrep -n "$SAMPLE_HEADER" | cut -f1 -d":")

echo "FASTQ_INDEX: $FASTQ_INDEX"
echo "SAMPLE_INDEX: $SAMPLE_INDEX"

if [ -n "$MACHINES" ]; then
    echo "Running on: $MACHINES"
    COMPUTE_MACHINES=" -S $MACHINES "
else
    echo "Running locally on $HOSTNAME"
    COMPUTE_MACHINES=""
fi

DELIM=","
echo "Extracting Sample Matrix at $SAMPLE_MATRIX"
tail -n +2 $SAMPLE_MATRIX | tr "\t" "$DELIM" | \
    cut -d$DELIM -f$FASTQ_INDEX,$SAMPLE_INDEX | \
    parallel $COMPUTE_MACHINES --colsep "," -j $NCPU_NICE wget -P $OUTPUT_PATH"/"{1} {2} 1> $LOGFILES".out" 2> $LOGFILES".err"

echo "Done."


