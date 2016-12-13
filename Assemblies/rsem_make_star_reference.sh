#!/bin/bash
set -eu
source ../etc/load_configs.sh

if [ $# -lt 2 ]
    then
    echo "Usage:"
    echo $0" SPECIESNAME /path/to/iGenome"
    echo "Example:"
    SPECIES="human"
    GENOME="Assemblies/Homo_sapiens/NCBI/GRCh38/"
    echo $0" $SPECIES $GENOME"
    echo "Output:"
    echo "$ASSEMBLIES/runtime/"$SPECIES"_ref38/"$SPECIES"_0""*"
    exit -1
fi

SPECIES=$1
GENOME_PATH=$2

EXE="$RSEM_DIR/rsem-prepare-reference"
GTF="$ASSEMBLIES/"$GENOME_PATH"/Annotation/Genes/genes.gtf"
GENOME="$ASSEMBLIES/"$GENOME_PATH"/Sequence/WholeGenomeFasta/genome.fa"
OUTPUT="$ASSEMBLIES/runtime/"$SPECIES"_ref38/"$SPECIES"_0"

mkdir -p $( dirname $OUTPUT )
$EXE --gtf $GTF \
     --star \
     --star-path $STAR_PATH \
     -p 8 \
    $GENOME \
    $OUTPUT
