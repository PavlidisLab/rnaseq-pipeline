#!/bin/bash
set -eu
source ../../etc/load_configs.sh

if [ $# -eq 0 ]
    then
    SERIES="GSE123456"
    echo "Usage:"
    echo $0" $SERIES SEQUENCES1.fastq.gz,SEQUENCES2.fastq.gz... <Optional, SEQUENCES1_MATE.fastq.gz,SEQUENCES2_MATE.fastq.gz...>"    
    return 1
fi

&>2 echo "Launching: -->" $0 $@ &1>2

SERIES=$1
while [[ $SERIES == */ ]]; do
    # Cleaning up "$SERIES"
    SERIES=$(echo $SERIES | sed 's|/$||g')
    echo "WARNING: Please do not use trailing forward-slashes in $SERIES. Removing it..." 
done 

shift
FASTQ_GZ=$@

# Using aligner $STAR_EXE
STAR_GENOMEDIR=$(dirname $STAR_DEFAULT_REFERENCE) # TODO: Add parameter for this

# Create TMP directories.
TMPDIR="temporary/_STARtmp"
mkdir -p TMPDIR
UUID=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
TMPDIR="$TMPDIR/$UUID"

$STAR_EXE \
    --limitBAMsortRAM $STAR_MAX_BAM_RAM \
    --genomeDir $STAR_GENOMEDIR  \
    --outSAMunmapped Within \
    --outFilterType BySJout \
    --outSAMattributes NH HI AS NM MD XS \
    --outFilterMultimapNmax 20 \
    --outFilterMismatchNmax 999 \
    --outFilterMismatchNoverLmax 0.04 \
    --alignIntronMin 20 \
    --alignIntronMax 1000000 \
    --alignMatesGapMax 1000000  \
    --alignSJoverhangMin 8  \
    --alignSJDBoverhangMin 1  \
    --sjdbScore 1  \
    --runThreadN $NCPU_NICE  \
    --genomeLoad LoadAndKeep  \
    --outSAMtype BAM SortedByCoordinate  \
    --quantMode TranscriptomeSAM  \
    --outSAMheaderHD \@HD VN:1.4 SO:unsorted  \
    --readFilesCommand zcat  \
    --readFilesIn $FASTQ_GZ  \
    --outTmpDir "$TMPDIR" \
    --outStd BAM_SortedByCoordinate

#--outFileNamePrefix temporary/$SERIES/$SAMPLE \
# /space/bin/STAR-STAR_2.4.0h/bin/Linux_x86_64_static/STAR --genomeDir /misc/pipeline42/mbelmadani/rnaseq-pipeline/Assemblies/runtime/human_ref38  --outSAMunmapped Within  --outFilterType BySJout  --outSAMattributes NH HI AS NM MD  --outFilterMultimapNmax 20  --outFilterMismatchNmax 999  --outFilterMismatchNoverLmax 0.04  --alignIntronMin 20  --alignIntronMax 1000000  --alignMatesGapMax 1000000  --alignSJoverhangMin 8  --alignSJDBoverhangMin 1  --sjdbScore 1  --runThreadN 4  --genomeLoad LoadAndKeep  --outSAMtype BAM Unsorted  --quantMode TranscriptomeSAM  --outSAMheaderHD \@HD VN:1.4 SO:unsorted  --outFileNamePrefix temporary/I16R008_Neurogem/I16R008b06/I16R008b06  --readFilesCommand zcat  --readFilesIn /misc/pipeline42/NeuroGem/data/PD/raw_data//I16R008_Neurogem/I16R008b06/I16R008b06_01_R1.fastq.gz