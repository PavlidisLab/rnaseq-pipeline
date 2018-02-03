# Parallelism

About concurrent tasks and processing samples with parallelism.

## By CPUs

Parallel processing of samples can be acheived in a few ways. The most straightforward way is to increase the number of CPUs. Currently, `$NCPU_NICE` is used as both the number of concurrent samples processed and the number of processors RSEM can use per job. On a 16 CPUs, `NCPU_NICE=4` will max out cpu resources.

## Multiple servers

Samples are either processed one locally if `$MACHINES=""`, or they can be distributed across servers defined in `$MACHINES` (e.g. server1,server2.example.net,server3.sub.example.net). Make sure you can authenticate to the servers by SSH keys. See instructions on how to do so here: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2

The current configuration assumes each server has the same directory stucture, and the pipeline is installed/accessible on each server. This works best in the case of an Networked Filesystem (NFS), otherwise a work around would be to network mount the shared locations needed in `etc/common.cfg`. An sshfs mount (https://github.com/libfuse/sshfs) could also be used. 

## Scheduler

The scheduler will process `$NTASKS` series at a time when using `schedule_from_file.sh`. Each series/task will process samples using each the amount of CPUs and servers resources set in the `etc/common.cfg`. Make sure the CPUs for a single series doesn't use up all the resources if scheduling more than one task.
