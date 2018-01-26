#!/bin/bash
set -eu
##	SYNOPSIS:
##		qc_report.sh <GSE ID>
##
##	AUTHOR: 
##		Manuel Belmadani
##
##	DESCRIPTION: 
##		Produce a FastQC report on a set of input .fastq files
##	
##

source ../../etc/load_configs.sh

PROJECT=$1
OUTDIR=$METADATA"/"$PROJECT"/FastQCReports/"
mkdir -p $OUTDIR

## TODO: Ideally, find path where fastq are, call dirname, sort uniq, run on reach parent of fastqs
## Or, enforce consistent paths.

# FastQC
# TODO: Configurable thread count
# find $DATA/$PROJECT/ -name "*.fastq.gz" -exec gunzip -c  '{}' ';' | $FASTQC_EXE -t 16 /dev/stdin -o $OUTDIR --extract
find $DATA/$PROJECT/ -name "*.fastq.gz" -exec $FASTQC_EXE -t 16 {} -o $OUTDIR --extract \;
multiqc $OUTDIR

