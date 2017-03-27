#!/bin/bash

set -e

## Functions
err_report() {
    echo "Error on line $1"
}
trap 'err_report $LINENO' ERR

## Configurations
 
LOCATION="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

mkdir -p "$LOCATION/tmp"
configfile="$LOCATION/common.cfg"
configfile_secured="$LOCATION/tmp/common_"$(uuidgen)".cfg"
cp $configfile $configfile_secured

# Sanitize files
if egrep -q -v '^#|^[^ ]*=[^;]*' "$configfile"; then
  echo "Config file is unclean, cleaning it..." >&2

  # Save output to temporary directory.
  egrep '^#|^[^ ]*=[^;&]*' "$configfile" > "$configfile_secured"
  configfile="$configfile_secured"
fi

source $configfile
>&2 echo "Config file '$LOCATION/common.config' loaded."
