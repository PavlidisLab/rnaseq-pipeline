#!/bin/bash

#
# This script downloads a GSE metadata and produces a list of SRA and SRR pairs
# for downstream processing.
#

set -eu

cd "$(dirname "$0")"

if [ "$#" -ne 1 ]; then
    ACCESSION="GSE89692"
    echo "Description: "
    echo "Provide a GEO Series (GSE) identifier to download all fastq files from.."
    echo "Usage:"
    echo "$0 <ACCESSION>"
    echo "Example:"
    echo "$0 $ACCESSION"
    echo "   where $DATA/$ACCESSION would hold all the downloaded data."
    exit 1
fi

shellcheck_suppress () {
    # Suppress a shellcheck warning by adding something harmless to then end of a pipe
    tee;
};
export -f shellcheck_suppress

## ShellCheck specific
suppress_SC2001 () {
    # Suppress the echo|sed replacement warning for cases where native bash substitutions isn't enough.
    shellcheck_suppress ;
};
export -f suppress_SC2001

ACCESSION="$1"
RANK="$(echo "$ACCESSION" | sed 's|...$|nnn|g' | suppress_SC2001)"

# SOFTFILE="ftp://ftp.ncbi.nlm.nih.gov/geo/series/$RANK/$ACCESSION/soft/$ACCESSION""_family.soft.gz"
MINIML="ftp://ftp.ncbi.nlm.nih.gov/geo/series/$RANK/$ACCESSION/miniml/$ACCESSION""_family.xml.tgz"

DOWNLOAD_DIR="$DATA/$ACCESSION/METADATA"

if [ ! -z ${MODES+x} ] && [ -n "$MODES" ]; then
    echo "Propagating environment for modes $MODES" 1>&2
    PARALLEL_MODES=" --env MODES "
else
    PARALLEL_MODES=""
fi

# Download metadata files
mkdir -p "$DOWNLOAD_DIR"

MINIMLOUT="$DOWNLOAD_DIR/$ACCESSION.xml.tgz"
MINIMLXML="$DOWNLOAD_DIR/$ACCESSION.xml"

echo $MINIMLXML 1>&2

if [ ! -f "$MINIMLXML" ]
then
    wget -O "$MINIMLOUT" "$MINIML"
    echo "Extracting $MINIMLOUT" 1>&2
    tar -xvzf "$MINIMLOUT" --to-stdout > "$MINIMLXML"
else
    echo "MINIML xml file exists at $MINIMLXML." 1>&2
fi

METADATA_URL="http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term="

echo "Parsing MINIML xml at: $MINIMLXML" 1>&2
python parse_miniml.py "$MINIMLXML"
