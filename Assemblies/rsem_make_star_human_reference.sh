source ../etc/load_configs.sh

EXE="$RSEM_DIR/rsem-prepare-reference"
GTF="$ASSEMBLIES/Homo_sapiens/NCBI/GRCh38/Annotation/Genes/genes.gtf"
GENOME="$ASSEMBLIES/Homo_sapiens/NCBI/GRCh38/Sequence/WholeGenomeFasta/genome.fa"
OUTPUT="$ASSEMBLIES/runtime/human_ref38/human_0"

$EXE --gtf $GTF \
     --star \
     --star-path $STAR_PATH \
     -p 8 \
    $GENOME \
    $OUTPUT