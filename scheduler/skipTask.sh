#!/bin/bash
set -eu


if [ $# -lt 2 ]
  then
    SERIES="GSE123456"
    TASK="qc"
    echo "Usage:"
    echo "  $0 $SERIES $TASK "

    echo "Will write to commit/"$TASK"_"$SERIES".tsv"
    exit -1
fi


# Use download, qc, process, count for task.
SERIES=$1
TASK=$2

touch "commit/"$TASK"_"$SERIES".tsv"
