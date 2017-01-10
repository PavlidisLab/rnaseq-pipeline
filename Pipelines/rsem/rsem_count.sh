#!/bin/bash

if [ $# -lt 2 ] 
then
    echo "Usage: ./rsem_count PATHTOFILES <isoforms|genes>"
    exit
fi

FILES=$1
LEVEL=$2

EXE="/misc/pipeline42/NeuroGem/install/RSEM/rsem-generate-data-matrix"
EXE_TPM="/misc/pipeline42/NeuroGem/install/RSEM/rsem-generate-tpm-matrix"
EXE_FPKM="/misc/pipeline42/NeuroGem/install/RSEM/rsem-generate-fpkm-matrix"

cd $FILES

$EXE      *".$LEVEL.results" | sed "s|.$LEVEL.results||g" > countMatrix.$LEVEL
$EXE_TPM  *".$LEVEL.results" | sed "s|.$LEVEL.results||g" > tpmMatrix.$LEVEL
$EXE_FPKM *".$LEVEL.results" | sed "s|.$LEVEL.results||g" > fpkmMatrix.$LEVEL
