#!/bin/bash

source ../etc/load_configs.sh
set -eu

if [ $# -eq 0 ]
    then
    FILES="GSE123456"
    EXPECTED="14"
    echo "Usage:"
    echo $0' $FILES  $EXPECTED'
    echo "Example:"
    echo $0" $FILES  $EXPECTED"
    echo
    echo "Returns: The number of samples and pairs. Error if not equal to expected."
    exit
fi
 
FILES=$1
EXPECTED=$2

if [[ -d $FILES ]]; then
    # Path is a directory, no need to preprend $DATA directory.
    echo "Using files at path $FILES"
else
    # Look for files in $DATA.
    FILES=$DATA"/"$FILES
    echo "Searching for files in $DATA."
    if [[ -d $FILES ]]; then
	echo "Using files at path $FILES"
    else
	echo "No files found at $1 or $FILES."
	echo "Abort."
	exit 1
    fi
fi

nSEQUENCES=$(find $FILES -name "*$DEFAULT_MATE_SOURCE.fastq.gz"  | sed -e 's|.*\(GSM[0-9]\+\).*|\1|g'  | sort | uniq  | wc -l)
nMATES=$(find $FILES -name "*$DEFAULT_MATE_REPLACEMENT.fastq.gz"  | sed -e 's|.*\(GSM[0-9]\+\).*|\1|g'  | sort | uniq  | wc -l)

echo "$nSEQUENCES SEQUENCE FILES FOUND."
echo "$nMATES MATE FILES FOUND."

if [ $nMATES -gt 0 ]; then
    echo "LOG: Data appears to be paired-end"
    if [ $nSEQUENCES -ne $nMATES ]; then
	echo "WARNING: SEQUENCES AND MATES SHOULD BE EQUAL UNLESS BOTH PAIRED-END AND SINGLE-END SEQUENCES SAMPLES ARE MIXED."
    fi

    if [ $nSEQUENCES -eq $nMATES ]; then
	echo "OK: #Sequences == #Mates"
    fi
fi

if [ $EXPECTED -eq $nSEQUENCES ]; then
    echo "$FILES is OK."
else
    echo "$FILES 's sample count is not equal to expected count."
    echo "$EXPECTED !== $nSEQUENCES"
    exit -1
fi
