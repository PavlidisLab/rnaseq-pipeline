# Pavlidis Lab RNA-seq pipeline repository

TODO: Documentation

The documentation is still being written and tested. In the meantime, users interested in using this pipeline for RNASeq quantification should contact [@mbelmadani](https://github.com/mbelmadani) - manuel.belmadani@msl.ubc.ca for configuration assistance.

# General install instructions

## Getting started
Create a directory where you will clone this repository. From example `/home/username/Pipeline`

`mkdir -p /home/$(whoami)/Pipelines`

`cd /home/$(whoami)/Pipelines`
`git clone https://github.com/PavlidisLab/rnaseq-pipeline`


## Creating/Updating configuration
The bulk of how this pipeline works relies on a main configuration file (in etc/common.cfg) as well as "modes" to run tasks with modified configurations (see etc/modes/* for some examples).

To start, you can copy `etc/common.cfg.EXAMPLE` to `etc/common.cfg`. The `.EXAMPLE` file shows a set up where the pipeline is installed in `/home/$USERNAME/Pipelines/`. If you want to install it somewhere else, change the `$ROOT_DIR`. There's also a separate `RESULTS_DIR` and `SCRATCH_DIR` which you can either leave the same as `ROOT_DIR` or point to different locations. For example, we do this to avoid storing raw data in locations with limited storage, so we set `DATA=$SCRATCH_DIR/Data`, and we can change `$SCRATCH_DIR` to point to a location with more storage if needed.

## Getting the requirements

### Updating submodules
git submodule update --init --recursive

See Requirements/README.md

## Creating assemblies

See Assemblies/README.md

# Automated processing

## Using the scheduler to automatically download and process datasets with RSEM

Note: This steps requirement a virtual environment in `scheduler/` with packages such as spotify/luigi installed. Contact @mbelmadani if you need assistance with this.

This directory holds a scheduler to handle task processing and dependencies between tasks (e.g. making sure a series is download before attempting to process it.)

Please enter `scheduler/` and run included scripts from this location in order to schedule tasks. 
The scheduler can be started with `./start_scheduler.sh` and stopped with `./stop_scheduler.sh`.

We currently support scheduled processing of GEO or ArrayExpress datasets. All you need is an ID (of the form GSEnnnnn or E-MTAB-nnnnn) and the number of RNA-Seq samples expected.

Run `./schedule.sh` or `./schedule_from_file.sh` with not arguments for more information.

For example, `./schedule.sh CountGSE mouse,distributed --gse=GSE64978 --nsamples=10` would download, qc, process and generate count matrices for the GEO series `GSE64978`. 

# Manual processing

## Downloading data
See `scripts/`; run `./GSE_to_fastq.sh $ACCESSION` or `./arrayexpress_to_fastq.sh $ACCESSION`, where your accession is respectively a GEO series or an ArrayExpress identifier.

## Using the pipelines

In `Pipelines/`, you can see different flavors of pipelines. `Pipelines/rsem` is the most mature one, while `Pipelines/stringtie` has been used on limited occasions. 

### Pipelines/rsem

The directory includes scripts to process data with RSEM. If you've downloaded your data using GSE_to_fastq.sh or arrayexpress_to_fastq.sh methods, then most likely you'll want to use `./multiple_rsem.sh $ACCESSION $ACCESSION`. The first argument is the path to the data, and the second is the name of the series. If the data is downloaded into $DATA according to etc/common.cfg, then it's sufficient to use the `$ACCESSION` as the path; the script will know to look in $DATA. If the path is different, then the first argument should be the full path to the series directory.

