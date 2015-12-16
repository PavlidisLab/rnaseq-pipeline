#!/bin/bash

EXPERIMENT="bipolar"
INPUT="/misc/pipeline42/mbelmadani/rnaseq/"
if [ $# -lt 2 ]; then
    echo "Missing arguments"
    echo "First argument should be 'bipolar' or 'normal' "
    echo "Second argument should be the path to write files"
    echo "Example: ./SCRIPT bipolar /misc/pipeline42/mbelmadani/rnaseq/"
    exit
else
    EXPERIMENT=$1
    INPUT=$2
fi

HTSEQ="/home/mbelmadani/.local/bin/htseq-count"

REFSEQ="/misc/pipeline42/reference_data/hg19_Ensembl_iGenomes/Homo_sapiens/Ensembl/GRCh37/Annotation/Archives/archive-2013-03-06-14-23-04/Genes/gene_chr.gtf"

HTSEQ_SUBDIR="/HTSeqAlt/"

SAMPLES=$(ls -d $INPUT$EXPERIMENT/C*1)
SAMPLES=($SAMPLES)

SLICE_LENGTH=8
START=0
TERMINATE=0

while [ $TERMINATE -lt 1 ]
do
    SLICE=("${SAMPLES[@]:$START:SLICE_LENGTH}")
    
    if [ ${#SLICE[@]} -lt 1 ] 
    then
	TERMINATE=1
    fi

    let START=$START+$SLICE_LENGTH

    for SAMPLE_PATH in ${SLICE[@]}; do (
	    echo "Processing $SAMPLE_PATH"
	    
	    SAMPLE=$(basename $SAMPLE_PATH)
	    
	    BAMFILE=$SAMPLE_PATH"/StarAlign/alignmentAligned.out.bam"

	    OUTPUT=$SAMPLE_PATH$HTSEQ_SUBDIR
	    mkdir -p $OUTPUT
	    OUTPUT=$OUTPUT"output.count"
	    $HTSEQ -m intersection-nonempty -f bam -s no -a 50  $BAMFILE $REFSEQ > $OUTPUT 2> $OUTPUT".log"
	) 
    done
done
echo "Everything is done"

#htseq-count -m intersection-nonempty -s no -a 50  $BAMFILE $REFSEQ > HTSEQ_OUT/12n.count.bam 2> HTSEQ_OUT/12n.log; echo "DONE 12" 
#mkdir