#!/bin/bash
# set -eu

if [ -z "$1" ]; then
    echo "Usage: wipe_gse <GSE>"
    echo "A GSE identifier must be provided."
    exit 1
fi

source ../etc/load_configs.sh

GSE=$1

DELDATA="$DATA/$GSE"
DELLOGS="$LOGS/$GSE"
DELCOMMIT="commit/" 
DELCOMMITNAME="'*$GSE.tsv'"
DELCOMMITCOUNT=$(find $DELCOMMIT -name $DELCOMMITNAME | wc -l)

echo "## Delete data at $DELDATA"
rm -rf "$DELDATA"

echo "## Delete logs at $DELLOGS"
rm -rf "$DELLOGS"

echo "## Delete commits at $DELCOMMIT ($DELCOMMITCOUNT files)."
find "$DELCOMMIT" -name "$DELCOMMITNAME" -exec rm {} \;

echo "Press any key to continue."
read dummy </dev/tty
