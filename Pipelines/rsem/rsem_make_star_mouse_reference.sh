EXE="/misc/pipeline42/NeuroGem/install/RSEM/rsem-prepare-reference"
STAR="/space/bin/STAR-STAR_2.4.0h/bin/Linux_x86_64_static/"
GTF="/misc/pipeline42/NeuroGem/assembly/mouse/Mus_musculus/Ensembl/GRCm38/Annotation/Genes/genes.gtf"
GENOME="/misc/pipeline42/NeuroGem/assembly/mouse/Mus_musculus/Ensembl/GRCm38/Sequence/WholeGenomeFasta/genome.fa"
OUTPUT="/misc/pipeline42/NeuroGem/pipeline/runtime/mouse_ref38/mouse_0"

$EXE --gtf $GTF \
     --star \
     --star-path $STAR \
     -p 16 \
    $GENOME \
    $OUTPUT