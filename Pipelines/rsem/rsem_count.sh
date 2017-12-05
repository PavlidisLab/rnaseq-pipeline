#!/bin/bash
set -eu
cd $(dirname $0) 
source ../../etc/load_configs.sh

if [ $# -lt 2 ] 
then
    echo "Usage: ./rsem_count PATHTOFILES <isoforms|genes>"
    exit
fi

FILES=$1"/"
LEVEL=$2

# Check if directory needs "DATA" path appended.
if [ -d $FILES ]; then 
    #OK
    touch /dev/null
else
    FILES=$QUANTDIR/$1
fi
echo "INFO: COUNTING FILES AT $FILES"


EXE="$RSEM_DIR""/rsem-generate-data-matrix"
EXE_TPM="$RSEM_DIR""/rsem-generate-tpm-matrix"
EXE_FPKM="$RSEM_DIR""/rsem-generate-fpkm-matrix"

cd $FILES

printf $LEVEL > countMatrix.$LEVEL
printf $LEVEL > tpmMatrix.$LEVEL
printf $LEVEL > fpkmMatrix.$LEVEL

$EXE      *".$LEVEL.results" | sed "s|.$LEVEL.results||g" | sed 's|"||g' >> countMatrix.$LEVEL
$EXE_TPM  *".$LEVEL.results" | sed "s|.$LEVEL.results||g" | sed 's|"||g' >> tpmMatrix.$LEVEL
$EXE_FPKM *".$LEVEL.results" | sed "s|.$LEVEL.results||g" | sed 's|"||g' >> fpkmMatrix.$LEVEL
