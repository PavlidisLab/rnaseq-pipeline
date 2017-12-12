#!/bin/bash

set -eu
cd $(dirname $0) 
source ../../etc/load_configs.sh
mkdir -p $LOGS/$(basename $0)

echo " In $0, modes are: $MODES "

if [ $# -eq 0 ]
    then
    SERIES="GSE123456"
    echo "Usage:"
    echo $0" $SERIES SEQUENCES1.fastq.gz,SEQUENCES2.fastq.gz... <Optional, SEQUENCES1_MATE.fastq.gz,SEQUENCES2_MATE.fastq.gz...>"    
    exit
fi
echo "Launching: -->" $0 $@ " |  $# arguments."
RSEM_EXE="$RSEM_DIR/rsem-calculate-expression"
REFERENCE=$STAR_DEFAULT_REFERENCE

SERIES=$1

while [[ $SERIES == */ ]]; do
    # Cleaning up "$SERIES"
    SERIES=$(echo $SERIES | sed 's|/$||g')
    echo "WARNING: Please do not use trailing forward-slashes in $SERIES. Removing it..." 
done 

SAMPLE=$(echo $2 | sed "s|.*$SERIES\/|\/|g" | sed "s|\/\/|\/|g" | cut -d"/" -f2) # Grab whatever trails $SERIES until the next forward slash.
echo "SampleID: $SAMPLE"

OUTPUT="$QUANTDIR/$SERIES/$SAMPLE"
TMP="$TMPDIR/$SERIES/$SAMPLE"

mkdir -p $OUTPUT
mkdir -p $TMP

SEQUENCES=$2
PAIRED_END=""
MATE=""

BAMFILES=""
if [ $STAR_KEEP_BAM -eq 1 ]; then
	BAMFILES=" --keep-intermediate-files "
fi

if [ $# -gt 2 ] && [ "$3" != "{2}" ]; then
    echo " Called for paired-end data."
    PAIRED_END=" --paired-end "
    MATES=$3

    CMD=$(echo $RSEM_EXE \
	-p "$NCPU_NICE" \
	--star-gzipped-read-file \
	--time \
	--star \
	--star-path $STAR_PATH \
	--temporary-folder $TMP \
	$PAIRED_END \
	" $SEQUENCES $MATES " \
	$REFERENCE \
	$OUTPUT \
	"--star-shared-memory LoadAndRemove $BAMFILES "
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
	" --star-shared-memory LoadAndRemove $BAMFILES "
    )    
fi

echo "Launching" $CMD #| tee $LOGS/$0/$SERIES.log
echo "Launching" $CMD > $LOGS/$(basename $0)/$SERIES.log

echo  "Sequences:" $SEQUENCES >> $LOGS/$(basename $0)/$SERIES.log
echo  "Mates:" $$MATES >> $LOGS/$(basename $0)/$SERIES.log

$CMD >> $LOGS/$(basename $0)/$SERIES.log 2> $LOGS/$(basename $0)/$SERIES.err
