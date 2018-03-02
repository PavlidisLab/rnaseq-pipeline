#!/bin/bash
set -eu

source ../etc/load_configs.sh

SERIES=$1
OUTPUT=$METADATA/$SERIES

mkdir -p $OUTPUT

for x in $(find $DATA/$SERIES -name "*.fastq.gz"); do 
	echo "$x,"$(unpigz -p 8 -c $x | wc -l ) >> $OUTPUT/$SERIES".readcount"
done



