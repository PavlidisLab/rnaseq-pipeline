#!/bin/bash
set -ue
source ../../etc/load_configs.sh

#
# Queue a job on a Sun Grid Engine setup.
# Example: qsub queue_wonderdump.sh SRR1553500 my_output
 
#$ -S /bin/bash
#$ -cwd
#$ -o SGE_OUT/output
#$ -e SGE_OUT/error
#$ -q all.q
#$ -l qname=all.q

(time sh $WONDERDUMP_EXE $1 $2) &> SGE_OUT/$1.time
