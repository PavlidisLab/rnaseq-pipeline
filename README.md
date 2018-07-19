# Pavlidis Lab RNA-seq pipeline repository

This documentation is principally written to support the Pavlidis Lab, and we're still updating it. But this pipeline should be fairly easy to configure on any Linux servers using these instructions. External users interested in using this pipeline for RNASeq quantification should contact [@mbelmadani](https://github.com/mbelmadani) - manuel.belmadani@msl.ubc.ca if troubleshooting assistance is needed.


# General install instructions

## Downloading and installing
Create a directory where you will clone this repository. From example `/home/username/Pipeline`

```
mkdir -p /home/$(whoami)/Pipelines
cd /home/$(whoami)/Pipelines
git clone https://github.com/PavlidisLab/rnaseq-pipeline
```

Please see [Requirements/README.md](https://github.com/PavlidisLab/rnaseq-pipeline/blob/master/Requirements/README.md) for information on how to set up the different requirements for this pipeline.

If you already have them installed on your machine, you can simply edit the configuration file described in the next section to point to existing executables.

## Requirements
See [README in Requirements](https://github.com/PavlidisLab/rnaseq-pipeline/blob/master/Requirements/README.md)

## Assemblies
Once the Requirements are configured, see [README in Assemblies](https://github.com/PavlidisLab/rnaseq-pipeline/blob/master/Assemblies/README.md)


# Getting started

## Creating/Updating configuration
The most important step to get this pipeline working is to set your configuration file.

The bulk of how this pipeline works relies on a main configuration file (in etc/common.cfg) as well as "modes" to run tasks with modified configurations (see `etc/modes/*` for some examples).

To start, you can copy `etc/common.cfg.EXAMPLE` to `etc/common.cfg`. The `.EXAMPLE` file shows a set up where the pipeline is installed in `/home/$USERNAME/Pipelines/`. If you want to install it somewhere else, change the `$ROOT_DIR`. There's also a separate `RESULTS_DIR` and `SCRATCH_DIR` which you can either leave the same as `ROOT_DIR` or point to different locations. For example, we do this to avoid storing raw data in locations with limited storage, so we set `DATA=$SCRATCH_DIR/Data`, and we can change `$SCRATCH_DIR` to point to a location with more storage if needed.

## Using modes

Modes are configuration files that are loaded after `common.cfg` to override the default settings, for example changing the download directory, or increasing the CPU count. See [etc/README.md](https://github.com/PavlidisLab/rnaseq-pipeline/blob/master/etc/README.md) or have a look at some [existing examples](https://github.com/PavlidisLab/rnaseq-pipeline/blob/master/etc/modes/).

# Automated processing

## Using the scheduler to automatically download and process datasets with RSEM

See scheduler/README.md

# Manual processing

## Downloading data
See `scripts/`; run `./GSE_to_fastq.sh $ACCESSION` or `./arrayexpress_to_fastq.sh $ACCESSION`, where your accession is respectively a GEO series or an ArrayExpress identifier.

## Using the pipelines

In `Pipelines/`, you can see different flavors of pipelines. `Pipelines/rsem` is the most mature one, while `Pipelines/stringtie` has been used on limited occasions. 

### Pipelines/rsem

The directory includes scripts to process data with RSEM. If you've downloaded your data using `GSE_to_fastq.sh` or `arrayexpress_to_fastq.sh` methods, then most likely you'll want to use `./multiple_rsem.sh $ACCESSION $ACCESSION` (since the input data directory in `$DATA/` will be the accession name, and the script knows to look in `$DATA`, both parameters are the same.) The first argument is the path to the data, and the second is the name of the series. If the data is downloaded into `$DATA` according to [etc/common.cfg](https://github.com/PavlidisLab/rnaseq-pipeline/blob/master/etc/commong.cfg), then it's sufficient to use the `$ACCESSION` as the path; the script will know to look in `$DATA`. If the path is different, then the first argument should be the full path to the series directory.

