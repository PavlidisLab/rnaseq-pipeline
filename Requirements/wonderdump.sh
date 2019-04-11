#!/bin/bash

#
# Wonderdump is a workaround to download SRA files directly
# when fastq-dump internet connection does not work. For example on Bash on Windows.
#
# Usage:
#   wonderdump SRR1553500 -X 10000

set -ue

cd "$(dirname "$0")"
source ../etc/load_configs.sh

# ASSUMING CONFIGURATION FILE HAS $FASTQDUMP_EXE

# The first parameter must be the SRR number.
SRR=$1

# This is where we will store the file.
SRA_DIR=$2
echo "SRR/DESTINATION: $SRR $SRA_DIR"

# Make the directory if it does not exist.
mkdir -p "$SRA_DIR"

# Create the full path to the file.
SRA_FILE="$SRA_DIR/$SRR.sra"
TMP_FILE="$SRA_DIR/$SRR.tmp"

LOGDIR="$LOGS/""$(basename "$0")""/""$(basename $(dirname "$SRA_DIR"))""/""$(basename "$SRA_DIR")""/""$SRR"
mkdir -p "$LOGDIR"

# Download only if it does not exist.
if [ ! -f "$SRA_FILE" ];
then
    PATH1=${SRR:0:6}
    PATH2=${SRR:0:10}
    echo "*** downloading: $SRA_FILE"
    echo "wget ftp://ftp-trace.ncbi.nih.gov/sra/sra-instant/reads/ByRun/sra/SRR/${PATH1}/${PATH2}/${SRR}.sra -O $TMP_FILE"
    wget "ftp://ftp-trace.ncbi.nih.gov/sra/sra-instant/reads/ByRun/sra/SRR/""${PATH1}""/""${PATH2}""/""${SRR}"".sra" -O "$TMP_FILE"
    mv "$TMP_FILE" "$SRA_FILE"
fi


# Download for backfilling purposes.
SAMPLE_ACCESSION=$(echo "$SRA_DIR" | rev | cut -f1,2 -d"/" | rev)
HEADERS_DIR="$FASTQHEADERS_DIR""/""$SAMPLE_ACCESSION"
mkdir -p "$HEADERS_DIR"

# Shift paramters
shift

# Are there parameters left.
if [ "$#" -gt "0" ]
then
    # Clear any existing headers
    find "$HEADERS_DIR""/" -name "$SRR""*fastq.header" -type f -delete

    # Run the fastq-dump.
    if [ "$FASTQDUMP_BACKFILL" == "0" ]; then
	echo "[INFO] Using Standard fastq-dump mode"
	CMD="$FASTQDUMP_EXE $SRA_FILE --outdir $SRA_DIR --gzip --skip-technical $FASTQDUMP_READIDS --dumpbase $FASTQDUMP_SPLIT --clip"
	$CMD > "$LOGDIR"".fastqdump.out" 2> "$LOGDIR"".fastqdump.err"
	
	# Take raw data and bacfill header
	find "$SRA_DIR""/" -name "*.fastq.gz" -exec bash -c 'zcat $1 | head -n1 > $2/$(basename ${1/.fastq.gz/}).fastq.header' _ {} "$HEADERS_DIR"  \;
    else 
	echo "[INFO] Using backfill mode"
	CMD="$FASTQDUMP_EXE $SRA_FILE --outdir $HEADERS_DIR --skip-technical $FASTQDUMP_READIDS --dumpbase $FASTQDUMP_SPLIT --clip"
	$CMD > "$LOGDIR"".fastqdump.out" 2> "$LOGDIR"".fastqdump.err"

	# Copy headers
	find "$HEADERS_DIR""/" -name "$SRR""*fastq" -exec bash -c 'head -n1 "$1"  > "${1/.fastq/}".fastq.header' _ {}  \;

	# Clear raw data	
	find "$HEADERS_DIR""/" -name "$SRR""*fastq" -type f -delete
    fi
fi
