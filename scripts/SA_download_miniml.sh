#!/bin/bash

set -eu
cd $(dirname $0) 
source ../etc/load_configs.sh

ACCESSION=$1
PLATFORM=$2
RANK=$(echo $ACCESSION | sed 's|...$|nnn|g')

DATA="$DATA""/SpecialCases"
mkdir -p $DATA

MINIML="ftp://ftp.ncbi.nlm.nih.gov/geo/series/$RANK/$ACCESSION/miniml/$ACCESSION""_family.xml.tgz"
FILE_TGZ="my.xml.tgz"
XML="my.xml"

wget -O $FILE_TGZ $MINIML
tar -xvzf $FILE_TGZ --to-stdout > $XML



METADATA_URL="http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term="
python parse_minimlPF.py $XML $PLATFORM \
    | cut -f1 -d" " \
    | xargs -n1 -I@ wget -qO- "$METADATA_URL""@" \
    | grep -v "SampleName" \
    | grep -v "^$" \
    | cut -f1,30 -d"," \
    | sort \
    | uniq \
    | parallel --colsep ',' -P $NCPU_NICE --jobs $NCPU_NICE $WONDERDUMP_EXE {1} "$DATA/$ACCESSION""_""$PLATFORM"/{2}

