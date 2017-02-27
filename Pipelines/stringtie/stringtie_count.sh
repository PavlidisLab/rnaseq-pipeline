#!/bin/bash
set -eu
cd $(dirname $0)
source ../../etc/load_configs.sh

if [ $# -ne 1 ] 
then
    echo "Usage: $0 PATHTOFILES"
    echo "Outputs isform and gene level counts"
    exit
fi

FILES=$1

EXE="prepDE"
$EXE -i $FILES -g "$FILES/gene_count_matrix.csv" -t "$FILES/transcript_count_matrix.csv"

