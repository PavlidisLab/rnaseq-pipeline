#!/bin/bash

source ../etc/load_configs.sh &> /dev/null
set -eu

if [ "$#" -ne 1 ]; then
    ACCESSION="GSE12345"
    echo "Usage:"
    echo "$0 <ACCESSION>"    
    echo "Description: "
    echo "Gather and store STAR alignment logs."
    echo "Example:"
    echo "$0 $ACCESSION"
    echo "   where $TMPDIR/$ACCESSION would hold all the temporary data."
    exit 42
fi

### Get the header of a .gz file
function fcat(){ echo "$1" && cat "$1" && echo "" ;  }; # FIXME: Is this still necessary?
export -f fcat;

GSE=$1 # GSE ID

OUTDIR="$METADATA"/"$GSE"
mkdir -p "$OUTDIR"

find "$TMPDIR"/"$GSE"/ -name "*Log.final.out" -exec bash -c 'fcat "$1"' _ {} \; >> "$OUTDIR"/"$GSE".alignment.metadata
