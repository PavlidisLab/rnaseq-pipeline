#!/bin/bash
source ../etc/load_configs.sh
set -eu

ACCESSION="$1" # GSEXXXXXXX
RANK="$(echo "$ACCESSION" | sed 's|...$|nnn|g' | suppress_SC2001)"
DOWNLOAD_DIR="$DATA/$ACCESSION/METADATA"
MINIMLOUT="$DOWNLOAD_DIR/$ACCESSION.xml.tgz"
MINIMLXML="$DOWNLOAD_DIR/$ACCESSION.xml"

LOGPREFIX="$DOWNLOAD_DIR""/Logs/"
TMPDIR="$DOWNLOAD_DIR""/tmp/"
mkdir -p "$LOGPREFIX"
mkdir -p "$TMPDIR"

MINIML="ftp://ftp.ncbi.nlm.nih.gov/geo/series/$RANK/$ACCESSION/miniml/$ACCESSION""_family.xml.tgz"
METADATA_URL="http://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term="

if [ ! -f "$MINIMLXML" ]
then
    wget -O "$MINIMLOUT" "$MINIML"
    echo "Extracting $MINIMLOUT"
    tar -xvzf "$MINIMLOUT" --to-stdout > "$MINIMLXML"
else
    echo "MINIML xml file exists at $MINIMLXML."
fi

echo "Parsing MINIML xml at: $MINIMLXML"

PART1="$TMPDIR""sample_platform_srx.part"
PART2="$TMPDIR""sample_run.part"
PART3="$TMPDIR""run_header.part"
PARTS_MERGED="$TMPDIR""merged_parts"
OUTPUT_HEADER_TABLE="$FASTQHEADERS_DIR""/""$ACCESSION"".fastq-headers-table.txt"
python fastqheader_tables.py "$MINIMLXML" > "$PART1"

echo "Platform relation at $PART1"
echo "Sample-Run relation at $PART2"
cat "$PART1" \
    | cut -f1 -d" " \
    | xargs -n1 -I@ wget -qO- "$METADATA_URL""@"  2>> "$LOGPREFIX""wget.err" \
    | grep -v "SampleName" \
    | grep -v "^$" \
    | cut -f1,30 -d","  \
    | sort \
    | uniq \
    | awk 'BEGIN{FS=","}{print $2"/"$1}' > "$PART2"

# Considerations"
#   Do we care about PE headers?
#   Do we was to list the individual runs?
#   
echo "Storing run headers at $PART3"
cat "$PART2" \
    | xargs -I@ bash -c 'set -eu; sed "s|\(.*\)|$(echo $1 | cut -f2 -d"/")\t\1|g" $2/$3/$1_1.fastq.header || echo -e "$(echo $1 | cut -f2 -d"/")\tFAILURE"' _ @  $FASTQHEADERS_DIR $ACCESSION \
    | tr " " "\t"   > "$PART3"

#   | awk 1 ORS=";;;"
echo "Merging parts at $PARTS_MERGED"
join -2 1 -1 4  <(join -e -j1  <(sort -k1 $PART1) <( cat $PART2 | tr "/" " " | sort -k1  )) $PART3 | sed 's| |,|g' | awk ' BEGIN{FS=","} { t = $1; $1 = $2; $2 = t; print; } ' > $PARTS_MERGED

echo "Writing final table output to $OUTPUT_HEADER_TABLE"
awk ' 
{
  if($4==k)
    printf("%s",";;;")
  else {
    if(NR!=1)
      print ""
    printf("%s\t",$1)
    printf("%s\t",$2)
    printf("%s\t",$3)
    printf("%s\t",$4)
  }
  for(i=5;i<NF;i++)
    printf("%s ",$i)
  printf("%s",$NF)
  k=$4
}
END{
print ""
}' $PARTS_MERGED > $OUTPUT_HEADER_TABLE
