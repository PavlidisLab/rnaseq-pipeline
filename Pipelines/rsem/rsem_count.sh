#!/bin/bash
set -eu
cd $(dirname $0) 
source ../../etc/load_configs.sh

if [ $# -lt 2 ] 
then
    echo "Usage: ./rsem_count PATHTOFILES <isoforms|genes>"
    exit
fi

FILES=$1
LEVEL=$2

EXE="$RSEM_DIR""/rsem-generate-data-matrix"
EXE_TPM="$RSEM_DIR""/rsem-generate-tpm-matrix"
EXE_FPKM="$RSEM_DIR""/rsem-generate-fpkm-matrix"

cd $FILES

echo $LEVELS > countMatrix.$LEVEL
echo $LEVELS > tpmMatrix.$LEVEL
echo $LEVELS > fpkmMatrix.$LEVEL

$EXE      *".$LEVEL.results" | sed "s|.$LEVEL.results||g" | sed 's|"||g' >> countMatrix.$LEVEL
$EXE_TPM  *".$LEVEL.results" | sed "s|.$LEVEL.results||g" | sed 's|"||g' >> tpmMatrix.$LEVEL
$EXE_FPKM *".$LEVEL.results" | sed "s|.$LEVEL.results||g" | sed 's|"||g' >> fpkmMatrix.$LEVEL
