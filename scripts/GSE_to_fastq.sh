#!/bin/bash
set -eu

cd "$(dirname "$0")" 
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
    exit -1
fi

mkdir -p "$LOGS""/""$(basename "$0")"

ACCESSION="$1"
RANK="$(echo "$ACCESSION" | sed 's|...$|nnn|g' | suppress_SC2001)"

# SOFTFILE="ftp://ftp.ncbi.nlm.nih.gov/geo/series/$RANK/$ACCESSION/soft/$ACCESSION""_family.soft.gz"
MINIML="ftp://ftp.ncbi.nlm.nih.gov/geo/series/$RANK/$ACCESSION/miniml/$ACCESSION""_family.xml.tgz"

DOWNLOAD_DIR="$DATA/$ACCESSION/METADATA"

PARALLEL_MACHINES=""
if [ -n "$MACHINES" ]; then
    echo "Using distributed mode on: $MACHINES"
    PARALLEL_MACHINES=" -S $MACHINES "
fi

if [ ! -z ${MODES+x} ] && [ -n "$MODES" ]; then
    echo "Propagating environment for modes $MODES"
    PARALLEL_MODES=" --env MODES "
else
    PARALLEL_MODES=""
fi

# Download metadata files
mkdir -p "$DOWNLOAD_DIR"

# SOFTOUT="$DOWNLOAD_DIR/$ACCESSION.soft.gz"
# SOFT="$DOWNLOAD_DIR/$ACCESSION.soft"

MINIMLOUT="$DOWNLOAD_DIR/$ACCESSION.xml.tgz"
MINIMLXML="$DOWNLOAD_DIR/$ACCESSION.xml"

###
## TODO: SOFT file probably not needed
# SOFTEXTRACTED="${$SOFTOUT%.*}"
#if [ ! -f "$SOFTEXTRACTED" ]
#then
#    wget -O $SOFTOUT $SOFTFILE
#    echo "Extracting $SOFTOUT"
#    gunzip -f $SOFTOUT 
#else
#    echo "Zipped SOFT File exists at $SOFTOUT"
#fi
####

if [ ! -f "$MINIMLXML" ]
then
    wget -O "$MINIMLOUT" "$MINIML"
    echo "Extracting $MINIMLOUT"
    tar -xvzf "$MINIMLOUT" --to-stdout > "$MINIMLXML"
else
    echo "MINIML xml file exists at $MINIMLXML."
fi

LOGPREFIX="$LOGS""/""$(basename "$0")""/""$ACCESSION"
mkdir -p "$(basename "$LOGPREFIX")"

echo "Launching parallel Wonderdump"
METADATA_URL="http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term="

echo "Parsing MINIML xml at: $MINIMLXML"
python parse_miniml.py "$MINIMLXML" \
    | cut -f1 -d" " \
    | xargs -n1 -I@ wget -qO- "$METADATA_URL""@"  2>> "$LOGPREFIX.wget.err" \
    | grep -v "SampleName" \
    | grep -v "^$" \
    | cut -f1,30 -d","  \
    | sort \
    | uniq \
    | parallel --halt now,fail=1 --colsep ',' $PARALLEL_MACHINES $PARALLEL_MODES -j "$NCPU_ALL" "$WONDERDUMP_EXE" {1} "$DATA/$ACCESSION/{2}" 1> $LOGPREFIX".out" 2> $LOGPREFIX".err" 

