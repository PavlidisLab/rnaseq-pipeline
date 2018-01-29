#!/bin/bash

source ../etc/load_configs.sh &> /dev/null
set -eu

### Get the header of a .gz file
function zhead(){ zcat $1 | head -n1 | tail -n1 ;   }; 
export -f zhead;

GSE=$1 # GSE ID

echo -e "ID"$MDL$GSE 
echo -e "Date"$MDL$(date)


# Print software information to metadata
echo ""
echo "# Software versions"
$FASTQC_EXE -v | tr " " "\t"
$FASTQDUMP_EXE --version | head -n2 | tail -n1 | rev | cut -f1 -d"/" | rev | sed "s|: ||g" | tr " " "\t"
$RSEM_DIR/rsem-calculate-expression --version | sed 's|Current version: ||g' | tr " " "\t"
$STAR_EXE --version | tr "_" "\t"


# Assembly information
echo ""
echo "# Assembly information"
ASSEMBLY_METADATA=$(echo $STAR_REFERENCE_GTF | sed "s|$ASSEMBLIES||g" | cut -f2,3,4 -d"/")
echo -e "Assembly"$MDL$ASSEMBLY_METADATA

# Run information
echo ""
echo "# Sequencing runs"
echo -e "RunIDs:"
find $DATA/$GSE/ -name "*.fastq.gz" -exec bash -c 'zhead "$0"' {} \; | cut -f1 -d" " | sort | uniq 

echo ""
echo "# Instrument/Batch information"
echo -e "Batch\tCount"
find $DATA/$GSE/ -name "*.fastq.gz" | xargs -I@ bash -c "zhead "@ | cut -f2 -d" " | sort | uniq -c | awk 'BEGIN{OFS="\t"}{print $2,$1}'

echo ""
echo "# Read lengths summary"
echo -e "Length\tCount"
find $DATA/$GSE/ -name "*.fastq.gz" | xargs -I@ bash -c "zhead "@ | cut -f3 -d" " | sort | uniq -c | awk 'BEGIN{OFS="\t"}{print $2,$1}'
