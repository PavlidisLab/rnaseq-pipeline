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

source ../etc/load_configs.sh

PROJECT=$1
OUTDIR=$METADATA"/"$PROJECT"/FastQCReports/"
mkdir -p $OUTDIR

#  Call FastQC
find $DATA/$PROJECT/ -name "*.fastq*" \
    | xargs -P $NCPU_ALL -I@ $FASTQC_EXE @ -o $OUTDIR --extract

# Aggregate reports
$MULTIQC $OUTDIR $TMPDIR/$PROJECT/
