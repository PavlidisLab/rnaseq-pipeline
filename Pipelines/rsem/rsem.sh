#!/bin/bash
set -eu

cd $(dirname $0) 
source ../../etc/load_configs.sh
echo " In $0, modes are: $MODES "

if [ $# -eq 0 ]
    then
    SERIES="GSE123456"
    echo "Usage:"
    echo $0" $SERIES SEQUENCES1.fastq.gz,SEQUENCES2.fastq.gz... <Optional, SEQUENCES1_MATE.fastq.gz,SEQUENCES2_MATE.fastq.gz...>"    
    exit
fi
echo "Launching: -->" $0 $@
RSEM_EXE="$RSEM_DIR/rsem-calculate-expression"
REFERENCE=$STAR_DEFAULT_REFERENCE

SERIES=$1

while [[ $SERIES == */ ]]; do
    # Cleaning up "$SERIES"
    SERIES=$(echo $SERIES | sed 's|/$||g')
    echo "WARNING: Please do not use trailing forward-slashes in $SERIES. Removing it..." 
done 

# SAMPLE=$(echo $(basename $2) | sed 's/,.*//g' | sed 's/.fastq.gz//g')
# SAMPLE=$(echo $2 | sed "s|.*$SERIES|$SERIES|g" | sed  "s|.*$SERIES\/?\(.*\)|\\1|g" | sed "s|\/.*||" ) 
SAMPLE=$(echo $2 | sed "s|.*$SERIES\/|\/|g" | sed "s|\/\/|\/|g" | cut -d"/" -f2) # Grab whatever trails $SERIES until the next forward slash.
echo "SampleID: $SAMPLE"

OUTPUT="quantified/$SERIES/$SAMPLE"
TMP="temporary/$SERIES/$SAMPLE"

mkdir -p $OUTPUT
mkdir -p $TMP

SEQUENCES=$2
PAIRED_END=""
MATE=""

if [ $# -gt 3 ] 
then
    echo " Called for paired-end data."
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
	" --keep-intermediate-files "

)
else
    echo " Called for single-end data.!"
    CMD=$(echo $RSEM_EXE \
	-p "$NCPU_NICE" \
	--star-gzipped-read-file \
	--time \
	--star \
	--star-path $STAR_PATH \
	--temporary-folder $TMP \
	" $SEQUENCES " \
	$REFERENCE \
	$OUTPUT \
	" --star-shared-memory LoadAndKeep " \
	" --keep-intermediate-files "
    )    
fi

echo $CMD   
$CMD 2>> "errors/$SERIES.txt" 1>> "logs/$SERIES.txt"
