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
echo "Launching: -->" $0 $@


# SAMPLE=$(echo $(basename $2) | sed 's/,.*//g' | sed 's/.fastq.gz//g')
# SAMPLE=$(echo $2 | sed "s|.*$SERIES|$SERIES|g" | sed  "s|.*$SERIES\/?\(.*\)|\\1|g" | sed "s|\/.*||" ) 
SERIES=$1
while [[ $SERIES == */ ]]; do
    # Cleaning up "$SERIES"
    SERIES=$(echo $SERIES | sed 's|/$||g')
    echo "WARNING: Please do not use trailing forward-slashes in $SERIES. Removing it..." 
done 

SAMPLE=$(echo $2 | sed "s|.*$SERIES\/|\/|g" | sed "s|\/\/|\/|g" | cut -d"/" -f2) # Grab whatever trails $SERIES until the next forward slash.
echo "SampleID: $SAMPLE"

OUTPUT="quantified/$SERIES/$SAMPLE"
TMP="temporary/$SERIES/$SAMPLE"

mkdir -p $OUTPUT
mkdir -p $TMP

PAIRED_END=""
MATE=""

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
    echo " Single-end sequences!"
    CMD=$( ./align_for_stringtie.sh $@ |
	$STRINGTIE_EXE  --bam - 
    )   
fi

echo $CMD 2>>  "error-$SERIES.txt" 1> count-"$SAMPLE"-"$SERIES".txt