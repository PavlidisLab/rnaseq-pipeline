
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

FASTQC_EXE="/home/bcallaghan/rnaseqproj/FastQC/fastqc -t 1"

#BEFORE_PATH="/home/bcallaghan/rnaseqproj/fastqs/hippocampus/"
AFTER_PATH=$2"/"$EXPERIMENT

# Get file names
SAMPLES=$(ls -d $AFTER_PATH"/"*_1 | xargs -n1 basename )
#BIPOLARS=$(ls -d $AFTER_PATH"bipolar/"*_1 | xargs -n1 basename )
#NORMALS=$(ls -d $AFTER_PATH"normal/"*_1 | xargs -n1 basename )

for SAMPLE in $SAMPLES; do (
    ROOT=$AFTER_PATH$"/"$SAMPLE"/"
    FILES=$ROOT""trimmed*
    OUTPUT=$ROOT""FastqcReports/

    # Run FastQC
    mkdir -p $OUTPUT
    
    echo "started" > $OUTPUT"status.txt"
    echo "Updating "$OUTPUT"status.txt"
    $FASTQC_EXE $FILES -o $OUTPUT --extract > $OUTPUT"fastqc.log"
    echo "completed" > $OUTPUT"status.txt"
    ) &
done

# Run FastQC
#$FASTQC_EXE /misc/pipeline42/mbelmadani/rnaseq/C11_1/trimmed_C11_1_* -o /misc/pipeline42/mbelmadani/rnaseq/C11_1/FastqcReports/ --extract