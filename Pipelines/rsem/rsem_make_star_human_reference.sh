EXE="/misc/pipeline42/NeuroGem/install/RSEM/rsem-prepare-reference"
STAR="/space/bin/STAR-STAR_2.4.0h/bin/Linux_x86_64_static/"
GTF="/misc/pipeline42/NeuroGem/assembly/human/Homo_sapiens/NCBI/GRCh38/Annotation/Genes/genes.gtf"
GENOME="/misc/pipeline42/NeuroGem/assembly/human/Homo_sapiens/NCBI/GRCh38/Sequence/WholeGenomeFasta/genome.fa"
OUTPUT="/misc/pipeline42/NeuroGem/pipeline/runtime/human_ref38/human_0"

$EXE --gtf $GTF \
     --star \
     --star-path $STAR \
     -p 8 \
    $GENOME \
    $OUTPUT