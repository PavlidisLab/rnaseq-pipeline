#!/bin/bash
set -eu

cd $(dirname $0)
source ../../etc/load_configs.sh

if [ $# -eq 0 ]
    then
    SERIES="GSE123456"
    echo "Usage:"
    echo "Using fastq files:"
    echo $0" $SERIES SEQUENCES1.fastq.gz,SEQUENCES2.fastq.gz... <Optional, SEQUENCES1_MATE.fastq.gz,SEQUENCES2_MATE.fastq.gz...>"    
    echo "Pre aligned (bam) files:"
    echo $0" $SERIES ALIGNMENT.bam --bam REFERENCE.gtf "
    exit
fi
echo "Launching script:" $0 
echo "Arguments:" $@


# Clean SERIES name
SERIES=$1
while [[ $SERIES == */ ]]; do
    # Cleaning up "$SERIES"
    SERIES=$(echo $SERIES | sed 's|/$||g')
    echo "WARNING: Please do not use trailing forward-slashes in $SERIES. Removing it..." 
done 

# Clean files path
FILES=$2
while [[ $FILES == *"//"* ]]; do
    # Cleaning up consecutive slashes in path
    FILES=$(echo $FILES | sed 's|//|/|g')
done

# Obtain SampleID
SAMPLE=$(echo $FILES | sed "s|.*$SERIES\/||g" | cut -d"/" -f1) # Grab whatever trails $SERIES until the next forward slash.
echo "SampleID: $SAMPLE"

OUTPUT="quantified/$SERIES/$SAMPLE"
mkdir -p $OUTPUT

PAIRED_END=""
ALIGN="./align_for_stringtie.sh"
BAM="FALSE"
echo "Sequencing type:"

if [ $# -eq 3 ] &&  [ "$3" == "{2}"  ]; then
    echo " Unpaired reads."
    set -- "${@:1:$(($#-1))}" # FIXME: multiple_stringtie.sh passes a {2} for cases with paired end. This gets rid of that, for now.
    echo "Preparing aligner with $ALIGN $@"
elif [ $# -eq 4 ] &&  [ "$3" == "--bam" ]; then
    echo " Bam file"
    ALIGN="echo"
    BAM="$FILES"
    STAR_REFERENCE_GTF=$4 # If an alternate GTF was provided, use it.

    set -- "${@:1:$(($#-1))}" # Pop
    set -- "${@:1:$(($#-1))}" # Pop
    echo "No need to align $@"

else
    echo " Paired reads."
    echo "Preparing aligner with $ALIGN $@"
fi

echo "Preparing quantification:"
echo "$STRINGTIE_EXE \
    -p \"$NCPU_NICE\" \
    -e \
    -o $OUTPUT/counts.gtf \
    -G $STAR_REFERENCE_GTF \
    -C $OUTPUT/covrefs-count.txt \
    --bam $BAM \
    2>  $OUTPUT/error.txt"

if [ "$BAM" == "FALSE" ]; then
    echo "Passing FASTQs to aligner "
    $ALIGN $@ |	
    $STRINGTIE_EXE \
	-p "$NCPU_NICE" \
	-e \
	-o $OUTPUT/counts.gtf \
	-G $STAR_REFERENCE_GTF \
	-C $OUTPUT/covrefs-count.txt \
	--bam - \
	2>>  $OUTPUT/error.txt    
else
    echo "Aligned BAM file directly"
    $STRINGTIE_EXE \
	-p "$NCPU_NICE" \
	-e \
	-o $OUTPUT/counts.gtf \
	-G $STAR_REFERENCE_GTF \
	-C $OUTPUT/covrefs-count.txt \
	--bam $BAM  \
	2>>  $OUTPUT/error.txt    
fi

echo "Done $SAMPLE ."