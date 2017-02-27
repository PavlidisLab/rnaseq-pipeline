#!/bin/bash
set -eu

cd $(dirname $0)
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

echo "Sequencing type:"
if [ $# -eq 3 ] &&  [ "$3" -eq "{2}"  ]; then
    echo " Unpaired reads."
    set -- "${@:1:$(($#-1))}" # FIXME: multiple_stringtie.sh passes a {2} for cases with paired end. This gets rid of that, for now.
else
    echo " Paired reads."
fi


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


echo "Done $SAMPLE ."