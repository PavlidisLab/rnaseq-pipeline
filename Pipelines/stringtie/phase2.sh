#!/bin/bash

while read -r bam; do 
    SAMPLE=$( echo $bam | cut -f5 -d"/")
    CMD="stringtie $bam -p10  -G quantified/mcgillBA24merged/merged.gtf -o merged$SAMPLE.gtf" 
    echo "Running: $CMD"
    time $CMD 
done < listofBA24bam
