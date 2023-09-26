# Pavlidis Lab RNA-seq pipeline repository

[![Python Package using Conda](https://github.com/PavlidisLab/rnaseq-pipeline/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/PavlidisLab/rnaseq-pipeline/actions/workflows/build.yml)

This documentation is principally written to support the Pavlidis Lab, and
we're still updating it. But this pipeline should be fairly easy to configure
on any Linux servers using these instructions. External users interested in
using this pipeline for RNA-Seq quantification should contact our
[helpdesk](mailto:MSL-PAVLAB-SUPPORT@LISTS.UBC.CA) if troubleshooting
assistance is needed.

## Features

 - source mechanism that support discovery of samples from GEO, SRA, ArrayExpress and Gemma (in-house curation database)
 - built with [STAR](https://github.com/alexdobin/STAR), [RSEM](https://github.com/deweylab/RSEM), [MultiQC](https://multiqc.info/), [FastQC](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/), and more
 - produces count and FPKM matrices suitable for analysis with R and Python
 - distributed via a workload manager thanks to [Bioluigi](https://github.com/pavlidisLab/bioluigi)
 - notify collaborators via [Slack API](https://api.slack.com/)
 - submit experiments defined in a Google Spreadsheet
 - web viewer to preview QC reports and download quantifications

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
conda env create -f environment.yml
conda activate rnaseq-pipeline
```

Build the shared memory cleanup tool:

```bash
make -C scripts
```

**Note:** We remove unused shared memory objects allocated by STAR in Slurm task prolog and
epilog scripts.

Build RSEM:

```bash
make -C contrib/RSEM
```

Install the pipeline Python package in the Conda environment:

```bash
pip install . # use -e if you want to edit the pipeline
```

Create a copy of `the example.luigi.cfg` file to `luigi.cfg`. It should work
as-is, but you might want to change the output location and the resources.

First, you need to start Luigi scheduler daemon. You can see the progress of
your tasks at http://localhost:8082/.

```bash
luigid
```

For convenience, we provide a `luigi-wrapper` script that sets the `--module`
flag to `rnaseq_pipeline.tasks` for you.

```bash
luigi-wrapper <task> <task_args>
```

## Setting up a genomic reference

The pipeline automatically generate the RSEM/STAR index and all that is
required is to drop the GTF annotations file and the primary assembly FASTA
files under `pipeline-output/genome/<reference_id>` subdirectory.

For example, you can setup a mouse reference from Ensembl by downloading the
following files under `pipeline-output/genomes/mm10_ensembl98`:

 - ftp://ftp.ensembl.org/pub/release-98/fasta/mus_musculus/dna/Mus_musculus.GRCm38.dna.primary_assembly.fa.gz
 - ftp://ftp.ensembl.org/pub/release-98/gtf/mus_musculus/Mus_musculus.GRCm38.98.gtf.gz

## Triggering tasks

The top-level task you will likely want to use is `rnaseq_pipeline.tasks.GenerateReportForExperiment`.

```bash
./luigi-wrapper rnaseq_pipeline.tasks.GenerateReportForExperiment --source geo --taxon mouse --reference mm10_ensembl98 --experiment-id GSE80745
```

The output is organized as follow:

```
pipeline-output/
    genomes/<reference_id>/                 # Genomic references
    references/<reference_id>/              # RSEM/STAR indexes
    data/<source>                           # FASTQs (note that GEO source uses SRA)
    data-qc/<experiment_id>/<sample_id>/    # FastQC reports
    aligned/<reference_id>/<experiment_id>/ # alignments and quantification results
    quantified/<reference_id>               # quantification matrices for isoforms and genes
    report/<reference_id>/<experiment_id>/  # MultiQC reports for reads and alignments
```

You can adjust the pipeline output directory by setting `OUTPUT_DIR` under
`[rnaseq_pipeline]` in the configuration.

```ini
[rnaseq_pipeline]
OUTPUT_DIR=/scratch/rnaseq-pipeline
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

## Web viewer

The pipeline comes with a Web viewer that provides convenient endpoints for
consulting QC reports.

When installing, add the `webviewer` extra require which will include [Flask](https://flask.palletsprojects.com/) and [gunicorn](https://gunicorn.org/):

```bash
pip install .[webviewer]
```

```bash
gunicorn rnaseq_pipeline.viewer:app
```

## Gemma integration

The RNA-Seq pipeline is capable of communicating with Gemma using its [RESTful API](https://gemma.msl.ubc.ca/resources/restapidocs/).

## External spreadsheet via Google Sheets API

The RNA-Seq pipeline can pull experiment IDs from a collaborative spreadsheet
through the Google Sheets API. This feature requires extra dependencies that
are supplied by the `gsheet` extra require:

```bash
pip install .[gsheet]
```

The `rnaseq_pipelines.tasks.SubmitExperimentsFromGoogleSpreadsheetToGemma` task
becomes available. We also have

```bash
submit-experiments-from-gsheet --spreadsheet-id <spreadsheet_id> --sheet-name <sheet_name>
```

The remote spreadsheet must be structured to have the following columns:

 - `experiment_id`, the Gemma exeriment short name
 - `priority`, the Luigi task priority, an integer
 - `data`, the status of the data, allowed values: `ok`, `resubmit` (forces a rerun), `needs attention`, all other values are ignored

Only experiments with strictly positive priority are scheduled.
