#!/bin/bash
set -eu
source ../../etc/load_configs.sh

timestamp() {
  date +"%T"
}

echo "Benchmarking" $1
start=$(timestamp)

LOCATION="$( cd "$( dirname "$1" )" && pwd )"
echo $LOCATION "<--- LOCATION"

DIR="$LOCATION/benchmark-logs"
mkdir -p $DIR
LOG="$DIR/benchmark-$1-$start.log"
ERR="$DIR/benchmark-$1-$start.err"

echo " Writing logs at $LOG"
echo "# Logs for $@" > $LOG
echo "# Err for $@" > $ERR

(time sh $@) 2> $ERR 1> $LOG

echo " Done for $0 $@ ."
