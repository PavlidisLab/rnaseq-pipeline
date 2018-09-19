#!/bin/bash
set -eu

GSE=$1
OUTPUT=/cosmos/data/pipeline-output/rnaseq/metadata/$GSE/$GSE.base.metadata

cd ..
./pipeline_metadata.sh $GSE > $OUTPUT
echo "Written to $OUTPUT"
