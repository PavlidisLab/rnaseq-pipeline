#!/bin/bash

source ../etc/load_configs.sh &> /dev/null
set -eu

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ] ; then
    ACCESSION="GSE12345"
    echo "Description: "
    echo "Gather and store pipeline parameter and sample information."
    echo "Usage:"
    echo "$0 <ACCESSION>"
    echo "Example:"
    echo "$0 $ACCESSION"
    echo "   where $TMPDIR/$ACCESSION would hold all the temporary data."
    exit -1
fi

if [ "$#" -eq 2 ]; then
    MDL=$2
fi
TAB="'\t'"

### Get the header of a .gz file
function get_series_sample_run(){ sed "s|$DATA/\?||g" - | sed 's|.fastq\(.gz\)\?||g' ; };
function zhead(){ zcat $1 | head -n1 | tail -n1 ;   }; 
function zhead4k(){ zcat $1 | head -n4000 ; }; 
function readCount4k(){ zcat $1 | head -n4000 | awk  'BEGIN{OFS="\t";} NR%4 == 2 {lengths[length($0)]++} END {for (l in lengths) {print l, lengths[l]}}' | paste <(echo $1)  - ; }; 
function printAssemblyForConfig() { source $1; echo $STAR_REFERENCE_GTF | sed "s|$ASSEMBLIES||g" | cut -f2,3,4 -d"/" ; };

export -f get_series_sample_run;
export -f zhead;
export -f zhead4k;
export -f readCount4k;

GSE=$1 # GSE ID

echo ""
echo "# Overview"
echo -e "ID"$MDL$GSE 
echo -e "Date"$MDL$(date)
echo -e "Number of files"$MDL$(find $DATA/$GSE/ -name "*.fastq.gz" | wc -l)
echo "###########################"

# Print software information to metadata
echo ""
echo "# Software versions"
$FASTQC_EXE -v | tr " " "\t"
$FASTQDUMP_EXE --version | head -n2 | tail -n1 | rev | cut -f1 -d"/" | rev | sed "s|: ||g" | tr " " "\t"
$RSEM_DIR/rsem-calculate-expression --version | sed 's|Current version: ||g' | tr " " "\t"
$STAR_EXE --version | tr "_" "\t"
echo "###########################"

# Assembly information
echo ""
echo "# Assembly information"
CONFIGFILE=$(ls -t $METADATA/$GSE/configurations/*.cfg | head -n1)
export CONFIGFILE=$CONFIGFILE
ASSEMBLY_METADATA=$(printAssemblyForConfig $CONFIGFILE)
echo -e "Assembly"$MDL$ASSEMBLY_METADATA
echo -e "Configurations"$MDL$CONFIGFILE
echo "###########################"

# Run information
echo ""
echo "# Sequencing runs"
echo -e "Run\tHeader:"
find $DATA/$GSE/ -name "*.fastq.gz" -exec bash -c 'echo -e "$0"'${TAB}'$(zhead "$0")' {} \; |  sort | uniq | get_series_sample_run
echo "###########################"

echo ""
echo "# Instrument/Batch information"
echo -e "Run\tBatch:"
find $DATA/$GSE/ -name "*.fastq.gz" | xargs -I@ bash -c 'echo -e "@"'${TAB}'$(zhead @ |  cut -f2 -d" ")' | sort | uniq | get_series_sample_run
echo "###########################"

echo ""
echo "# Read lengths summary (using header length= )."
echo -e "Run\tLengths:"
find $DATA/$GSE/ -name "*.fastq.gz" | xargs -I@ bash -c 'echo -e "@"'${TAB}'$(zhead @ |  cut -f3 -d" ")' | sort | uniq | get_series_sample_run
echo "###########################"

echo ""
echo "# Read lengths summary (Sampling first 4k rows)."
echo -e "Run\tCount\tSampledLength"
#paste <(find $DATA/$GSE/ -name "*.fastq.gz" | get_series_sample_run) <(find $DATA/$GSE/ -name "*.fastq.gz" | xargs -I@ bash -c "readCount4k "@)
find $DATA/$GSE/ -name "*.fastq.gz" | xargs -I@ bash -c "readCount4k "@ | sort | uniq |get_series_sample_run

echo "###########################"
