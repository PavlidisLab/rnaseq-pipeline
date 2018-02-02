# Using the automated scheduler

Note: This steps requirement a virtual environment in `scheduler/` with packages such as spotify/luigi installed. Contact @mbelmadani if you need assistance with this.

This directory holds a scheduler to handle task processing and dependencies between tasks (e.g. making sure a series is download before attempting to process it.)

Please enter `scheduler/` and run included scripts from this location in order to schedule tasks. 
The scheduler can be started with `./start_scheduler.sh` and stopped with `./stop_scheduler.sh`.

We currently support scheduled processing of GEO or ArrayExpress datasets. All you need is an ID (of the form GSEnnnnn or E-MTAB-nnnnn) and the number of RNA-Seq samples expected.

Run `./schedule.sh` or `./schedule_from_file.sh` with not arguments for more information.

For example, `./schedule.sh CountGSE mouse,distributed --gse=GSE64978 --nsamples=10` would download, qc, process and generate count matrices for the GEO series `GSE64978`. 
