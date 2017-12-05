#!/bin/bash
# set -eu
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
