#!/bin/bash
set -eu

cd $(dirname $0) 
source ../etc/load_configs.sh

if [ "$#" -ne 1 ]; then
    ACCESSION="GSE89692"
    echo "Description: "
    echo "Provide a GEO Series (GSE) identifier to download all fastq files from.."
    echo "Usage:"
    echo "$0 <ACCESSION>"
    echo "Example:"
    echo "$0 $ACCESSION"
    echo "   where $DATA/$ACCESSION would hold all the downloaded data."
    exit
fi

ACCESSION=$1
RANK=$(echo $ACCESSION | sed 's|...$|nnn|g')

SOFTFILE="ftp://ftp.ncbi.nlm.nih.gov/geo/series/$RANK/$ACCESSION/soft/$ACCESSION""_family.soft.gz"
MINIML="ftp://ftp.ncbi.nlm.nih.gov/geo/series/$RANK/$ACCESSION/miniml/$ACCESSION""_family.xml.tgz"

DOWNLOAD_DIR="$DATA/$ACCESSION/METADATA"

PARALLEL_MACHINES=""
if [ -n "$MACHINES" ]; then
    echo "Using distributed mode on: $MACHINES"
    PARALLEL_MACHINES=" -S $MACHINES "
fi

# Download SOFT file
mkdir -p $DOWNLOAD_DIR

SOFTOUT="$DOWNLOAD_DIR/$ACCESSION.soft.gz"
SOFT="$DOWNLOAD_DIR/$ACCESSION.soft"

MINIMLOUT="$DOWNLOAD_DIR/$ACCESSION.xml.tgz"
MINIMLXML="$DOWNLOAD_DIR/$ACCESSION.xml"

wget -O $SOFTOUT $SOFTFILE
wget -O $MINIMLOUT $MINIML

echo "Extracting $MINIMLOUT"
tar -xvzf $MINIMLOUT --to-stdout > $MINIMLXML

echo "Extracting $SOFTOUT"
gunzip -f $SOFTOUT 

LOGDIR=$LOGS/$0
mkdir -p $LOGDIR

echo "Launching parallel Wonderdump"
METADATA_URL="http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term="
python parse_miniml.py $MINIMLXML \
    | cut -f1 -d" " \
    | xargs -n1 -I@ wget -qO- "$METADATA_URL""@" 2> $LOGDIR/@ \
    | grep -v "SampleName" \
    | grep -v "^$" \
    | cut -f1,30 -d"," \
    | sort \
    | uniq \
    | parallel --colsep ',' $PARALLEL_MACHINES -P $NCPU_NICE --jobs $NCPU_NICE $WONDERDUMP_EXE {1} "$DATA/$ACCESSION/{2}"
