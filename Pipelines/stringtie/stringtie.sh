#!/bin/bash
set -eu
source ../../etc/load_configs.sh

if [ $# -eq 0 ]
    then
    SERIES="GSE123456"
    echo "Usage:"
    echo $0" $SERIES SEQUENCES1.fastq.gz,SEQUENCES2.fastq.gz... <Optional, SEQUENCES1_MATE.fastq.gz,SEQUENCES2_MATE.fastq.gz...>"    
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

# Obtain SampleID
SAMPLE=$(echo $2 | sed "s|.*$SERIES\/||g" | cut -d"/" -f1) # Grab whatever trails $SERIES until the next forward slash.
echo "SampleID: $SAMPLE"

OUTPUT="quantified/$SERIES/$SAMPLE"
mkdir -p $OUTPUT

PAIRED_END=""

echo "Sequence type:"
if [ $# -gt 9999999999 ] 
then
    echo "Not implemented"
    return 1
    exit
    
    echo " Paired end sequences. "
    PAIRED_END=" --paired-end "
    MATES=$3

    CMD=$(echo $RSEM_EXE \
	-p "$NCPU_NICE" \
	--star-gzipped-read-file \
	--temporary-folder $TMP \
	--time \
	--star \
	--star-path $STAR_PATH \
	$PAIRED_END \
	" $SEQUENCES $MATE " \
	$REFERENCE \
	$OUTPUT \
	"--star-shared-memory LoadAndKeep" \
)
else
    echo " Single-end sequences."
    set -- "${@:1:$(($#-1))}" # FIXME: multiple_stringtie.sh passes a {2} for cases with paired end.
                              # This gets rid of that, for now.

    echo "Align stringtie with " $@
    echo "./align_for_stringtie.sh $@ |	
    $STRINGTIE_EXE \
	-o $OUTPUT/counts.gtf \
	-G $STAR_REFERENCE_GTF \
	-C $OUTPUT/covrefs-count.gtf \
	--bam - \
	2>  $OUTPUT/error.txt"

    echo ' --- '
    ./align_for_stringtie.sh $@ |	
    $STRINGTIE_EXE \
	-p "$NCPU_NICE" \
	-e \
	-o $OUTPUT/counts.gtf \
	-G $STAR_REFERENCE_GTF \
	-C $OUTPUT/covrefs-count.txt \
	--bam - \
	2>  $OUTPUT/error.txt    
fi

echo "Done $SAMPLE ."