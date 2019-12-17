# Pavlidis Lab RNA-seq pipeline repository

This documentation is principally written to support the Pavlidis Lab, and we're still updating it. But this pipeline should be fairly easy to configure on any Linux servers using these instructions. External users interested in using this pipeline for RNASeq quantification should contact [@mbelmadani](https://github.com/mbelmadani) - manuel.belmadani@msl.ubc.ca if troubleshooting assistance is needed.

## Features

 - source mechanism that support GEO, SRA, ArrayExpress and Gemma (in-house curation database)
 - built with STAR, RSEM, MultiQC, FastQC
 - produces count and FPKM matrices suitable for analysis with R and Python
 - distributed via a workload manager

## Downloading and installing

Clone this repository:

```bash
git clone --recurse-submodules https://github.com/PavlidisLab/rnaseq-pipeline
cd rnaseq-pipeline
```

**Note:** We use a patched version of RSEM that honors the `$TMPDIR`
environment variable for its intermediate outputs, fix issues with moving files
across filesystems and uses STAR shared memory feature by default.

Create and activate a Conda environment with all the required software
dependencies:

```bash
conda env setup -f environment.yml
conda activate rnaseq-pipeline
```

Install the pipeline Python package in the Conda environment:

```bash
python setup.py install # use develop instead of install of you want to edit the pipeline
```

Create a copy of `the example.luigi.cfg` file to `luigi.cfg`. It should work
as-is, but you might want to change the output location.

For convenience, we provide a `luigi-wrapper` script that sets the `--module`
flag to `rnaseq_pipeline.tasks` for you.

```bash
./luigi-wrapper <task> <task_args>
```

## Setting up a genomic reference

The pipeline automatically generate the RSEM/STAR index and all that is
required is to drop the GTF annotations file and the primary assembly FASTA
files under `genome/<reference_id>` subdirectory.

For example, you can setup a mouse reference from Ensembl by downloading the
following files under `genomes/mm10_ensembl98`:

 - ftp://ftp.ensembl.org/pub/release-98/fasta/mus_musculus/dna/Mus_musculus.GRCm38.dna.primary_assembly.fa.gz
 - ftp://ftp.ensembl.org/pub/release-98/gtf/mus_musculus/Mus_musculus.GRCm38.98.gtf.gz

## Triggering tasks

```bash
./luigi-wrapper GenerateReportForExperiment --source geo --taxon mouse --reference mm10_ensembl98 --experiment-id GSE80745
```

## Setting up distributed computation

The pipeline is build upon [Bioluigi](https://github.com/PavlidisLab/bioluigi)
which supports dispatching external programs on a workload manager such as
[Slurm](https://slurm.schedmd.com/).

```ini
[bioluigi]
scheduler=slurm
scheduler_extra_args=[]
```

