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
if [ $# -eq 0 ]
    then
    FILES="GSE123456"
    echo "Usage:"
    echo $0' $FILES '
    echo "Example:"
    echo $0" $FILES "
    echo
    echo "Runs fastqc on the input directory, aggregated the results with multiqc."
    exit
fi

PROJECT=$1
OUTDIR=$METADATA"/"$PROJECT"/FastQCReports/"
OUTDIRMULTI=$METADATA"/"$PROJECT"/MultiQCReports/"
mkdir -p $OUTDIR
mkdir -p $OUTDIRMULTI

#  Call FastQC
echo "FastQC reports should be in $OUTDIR"
find $DATA/$PROJECT/ -name "*.fastq*" \
    | xargs -P $NCPU_NICE -I@ echo $FASTQC_EXE @ -o $OUTDIR --threads $NCPU_NICE --extract
echo "Done [fastqc]"

# Aggregate reports
echo "MultiQC reports should be in $OUTDIRMULTI"
$MULTIQC_EXE -o $OUTDIRMULTI $OUTDIR $TMPDIR/$PROJECT/
echo "Done [multiqc]"
