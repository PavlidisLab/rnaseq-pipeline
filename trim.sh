#!/bin/bash

EXPERIMENT="bipolar"
if [ $# -lt 2 ]; then
    echo "Missing arguments"
    echo "First argument should be 'bipolar' or 'normal' "
    echo "Second argument should be the path to write files"
    echo "Example: ./SCRIPT bipolar /misc/pipeline42/mbelmadani/rnaseq/"
    exit
else
    EXPERIMENT=$1
fi

DATAIN="/home/bcallaghan/rnaseqproj/fastqs/hippocampus/$EXPERIMENT/"
DATAOUT=$2"/$EXPERIMENT/"
echo "Writing output to:" $DATAOUT

FILESIN=$(ls $DATAIN/C* | xargs -n1 basename)

for FILE in $FILESIN
do
    echo "Input: $FILE"
    FILEOUT=$(echo "$FILE" | cut -f 1 -d '.')
    mkdir -p $DATAOUT$FILEOUT
    echo "started" > $DATAOUT$FILEOUT"/status.txt"
    java -jar /home/bcallaghan/rnaseqproj/Trimmomatic/trimmomatic-0.33.jar PE -threads 8 -phred64 -trimlog $DATAOUT$FILEOUT"/TRIMLOG" -basein $DATAIN"$FILE" -baseout $DATAOUT$FILEOUT"/trimmed_$FILE" ILLUMINACLIP:/home/bcallaghan/rnaseqproj/Trimmomatic/adapters/TruSeq3-PE.fa:2:30:12 && echo "complete" > $DATAOUT$FILEOUT"/status.txt"    
done

echo "Done!"
