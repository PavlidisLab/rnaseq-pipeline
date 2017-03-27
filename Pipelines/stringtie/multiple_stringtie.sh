#!/bin/bash
set -eu
source ../../etc/load_configs.sh

if [ $# -lt 2 ]
    then
    FILES="data/GSE123456/"
    SERIES="GSE123456"
    echo "Description: "
    echo "Provide a directory where sample runs are contained by distinct directories."
    echo "Usage:"
    echo "$0 <FILES> <SERIES>"
    echo "$0 <FILES> <SERIES> --paired-end"
    echo "$0 <FILES> <SERIES> --bam <REFERENCE.gtf> <Optional, BAM_REGEX>" 

    echo "Example:"
    echo "$0 $FILES $SERIES"
    echo "   where $FILES would have each sample under it's own directory."
    exit
fi
MATES=""
GTF=""
BAM=0
BAM_RE="*.bam"
if [ $# -gt 2  ] && [ "$3" == "--paired-end" ]; then
    echo " Using paired-end sequences. "
    MATES=" --paired-end "
elif [ $# -gt 2  ] && [ "$3" == "--bam" ]; then
    GTF=$4
    BAM=1
    if [ $# -ge 5 ]; then
	BAM_RE="$5"
    fi
    echo " Usign pre-aligned BAM files with refrence $GTF"
else
    if [ $# -gt 3 ]
    then
	echo "Too many arguments! Please check your command."
	echo "Argument count: $# "
	echo "$@"
	exit -1
    fi
    echo " Using single-end sequences. "
fi

FILES=$1
SERIES=$2
PARALLEL_MACHINES=""

if [ -n "$MACHINES" ]; then
    PARALLEL_MACHINES=" -S $MACHINES "
fi

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


#echo "Preparing memory..."
#$RSEM_DIR/rsem-star-load-shmem $STAR_EXE $REFERENCE $NCPU
#echo "Memory loaded."

if [ $BAM -eq 1 ]; then
    echo "Launching parallel Stringtie using BAM files: $FILES "
    find $FILES/ -name "*.bam"  | # Get samples
       grep "$BAM_RE" | # Just the bam the user wants filtered by regex.
       sort | # sorted
       uniq | # and unique.
       parallel $PARALLEL_MACHINES -P $NCPU_NICE --colsep ' ' \
	   $(pwd)/stringtie.sh $SERIES {1} --bam "$GTF" >> parallel-log.txt
else
    echo "Launching parallel Stringtie using FastQ files: $FILES "
    find $FILES/ -name "*.fastq.gz" -exec dirname {} \; | # Get samples directories 
          sort | # sorted
	  uniq | # and unique.
	  xargs -n1 -I % ./samplist.sh % $MATES | # Prepare sample (in pairs if needed).
	  parallel $PARALLEL_MACHINES -P $NCPU_NICE --colsep ' ' $(pwd)/stringtie.sh $SERIES {1} {2} >> parallel-log.txt
fi
    
#echo "Flushing memory..."
#$RSEM_DIR/rsem-star-clear-shmem $STAR_EXE $REFERENCE $NCPU
#echo "Memory flushed."

echo "Done."