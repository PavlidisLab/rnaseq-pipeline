#!/bin/bash
set -eu
source ../etc/load_configs.sh

if [ "$#" -ne 1 ]; then
    ACCESSION="SRP055008"
    echo "Description: "
    echo "Provide a project identifier to download all fastq files from.."
    echo "Usage:"
    echo "$0 <ACCESSION>"
    echo "Example:"
    echo "$0 $ACCESSION"
    echo "   where Data/$ACCESSION would hold all the downloaded data."
    exit
fi

ACCESSION=$1
DOWNLOAD_DIR="$DATA/$ACCESSION"
mkdir -p $DOWNLOAD_DIR

echo "Obtaining metadata."
METADATA=./$ACCESSION"_info.csv"

echo "Downloading from: http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term=$ACCESSION"
wget -O $METADATA "http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term=$ACCESSION"

PARALLEL_MACHINES=""
if [ -n "$MACHINES" ]; then
    echo "Using distributed mode on: $MACHINES"
    PARALLEL_MACHINES=" -S $MACHINES "
fi

echo "Obtaining individual FASTQs"
cut -f1 -d"," $METADATA | tail -n +2 | parallel $PARALLEL_MACHINES -P $NCPU_NICE --jobs $NCPU_NICE  -I@ $WONDERDUMP_EXE @ "$DOWNLOAD_DIR/"@ >> logs/parallel.log

