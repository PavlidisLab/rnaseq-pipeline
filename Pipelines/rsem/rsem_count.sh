#!/bin/bash

if [ $# -lt 2 ] 
then
    echo "Usage: ./rsem_count PATHTOFILES <transcript|gene>"
    exit
fi

FILES=$1
LEVEL=$2

EXE="/misc/pipeline42/NeuroGem/install/RSEM/rsem-generate-data-matrix"
EXE_TPM="/misc/pipeline42/NeuroGem/install/RSEM/rsem-generate-tpm-matrix"
EXE_FPKM="/misc/pipeline42/NeuroGem/install/RSEM/rsem-generate-fpkm-matrix"

$EXE      $FILES/*".$LEVEL.results" > $FILES/countMatrix.$LEVEL
$EXE_TPM  $FILES/*".$LEVEL.results" > $FILES/tpmMatrix.$LEVEL
$EXE_FPKM $FILES/*".$LEVEL.results" > $FILES/fpkmMatrix.$LEVEL
