#!/bin/bash
set -eu
source ../etc/load_configs.sh

LOGDIR=logs-luigi-$(echo $(hostname) | cut -f1 -d".")-$(whoami)
UUID=$(uuidgen)

mkdir -p PIDS
mkdir -p $LOGDIR

luigid --background --pidfile PIDS/$UUID --logdir $LOGDIR/ --state-path STATE --port $SCHEDULER_PORT
chmod -R a+rw $LOGDIR 
find $LOGDIR/ -exec  chmod a+rw {} \;
