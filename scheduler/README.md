# Using the automated scheduler

Note: This steps requirement a virtual environment in `scheduler/` with packages such as spotify/luigi installed. Contact @mbelmadani if you need assistance with this.

## Task workflow 

The scheduler handles task processing and automatically schedule dependencies required. The general flow of tasks is:

`[DownloadGSE] -> [QcGSE] -> [ProcessGSE] -> [CountGSE] -> [GatherMetadataGSE] -> [PurgeGSE]`

If ProcessGSE is requested for a series, the scheduler will attempt to complete DownloadGSE and QcGSE before running ProcessGSE, or halt the task if it fails completing the dependencies.

### DownloadGSE
Parameters:
```
  --gse=XXXXXX
```
Description:
  Download a GEO or ArrayExpress dataset. Downloaded files are stored in `$DATA`.


### QcGSE
Parameters:
```
  --gse=XXXXXX
  --nsamples=N
```
Description:

  Quality check for the download. Checks that there's exactly `N` samples. Automatically counts mate pairs together based on the filenames and according to the mate pair identifiers, `$DEFAULT_MATE_SOURCE` and `$DEFAULT_MATE_REPLACEMENT`, which should be "_1" and "_2" by default. A warning is printed if the number of mate-pairs are not equal, but doesn't halt as long as the number of samples is correct.

### ProcessGSE
Parameters:
```
  --gse=XXXXXX
```
Description:

  Process all samples from `XXXXXX` using STAR and RSEM. Typically, the first call to STAR will start loading the genome in shared memory so that it can be shared between other STAR processes, as long as they're aligning for the same genome. The human and mouse genomes requires about ~30Gbs in memory, so make sure to have more than 30Gbs of usuable memory for per genome and some extra for RSEM as well.
   Sample results are stored under `GSMyyyyyyy.results` files in `$QUANTDIR`, and the bam files are kept under `$TMPDIR` if  `$STAR_KEEP_BAM$ = 1` (Default: 0).
 
### CountGSE
Parameters:
```
  --gse=XXXXXX
  --scope={genes|isoforms}  
```
Description:

  Generate count matrices (Count, FPKM, TPM) from the results and stores them in `$COUNTDIR`. `--scope` determines if the matrices are done for genes or isoforms.
  
### GatherMetadataGSE

Parameters:
```
  --gse=XXXXXX
```

Description:
  Compute/fetch the proper metadata.
  * alignment_metadata.sh - Obtain STAR metadata by fetching.
  * pipeline_metadata.sh - Summary statistics on the datasets (Number of reads, parsed fastq headers, config file etc.)
  * qc_report.sh - Call fastqc on all files, and then multiqc.

### PurgeGSE

Parameters:
```
  --gse=XXXXXX
```
Description:

  Delete the raw data, alignments and temporary files for the series. Does not delete bam files if they were kept in $RESULTS (the quantification directory).
  
## Which tasks haven't been done on X dataset?
  
Progress can be checked with the `scheduler/progressReport.sh` script, which prints a tables of tasks and series processed.

The tasks can be reprocessed after being sucessfully completed by deleting files in the `commit/` directory. The files start with either `download_, qc_, process_, count_ or purge_` and are followed by the series identifier. Conversely, tasks can be skipped by leave a file of that format, or using `scheduler/skipTask.sh`. 

## Usage

Please enter `scheduler/` and run included scripts from this location in order to schedule tasks. 
The scheduler can be started with `./start_scheduler.sh` and stopped with `./stop_scheduler.sh`.

We currently support scheduled processing of GEO or ArrayExpress datasets. All you need is an ID (of the form GSEnnnnn or E-MTAB-nnnnn) and the number of RNA-Seq samples expected.

Run `./schedule.sh` or `./schedule_from_file.sh` with not arguments for more information.

For example, `./schedule.sh CountGSE mouse,distributed --gse=GSE64978 --nsamples=10` would download, qc, process and generate count matrices for the GEO series `GSE64978`. 

## Using the scheduler interface

When the scheduler is running, you can view monitor the status of tasks via a web browser at `localhost:$SCHEDULER_PORT`. If you're running the pipeline on a remote server without a web browser, connect to the server via an ssh tunnel:

` ssh -L 8079:localhost:8079 username@example.com -p123456 ` where 8079 is `$SCHEDULER_PORT` and `123456` is the server's ssh port (often 20 by default.)
