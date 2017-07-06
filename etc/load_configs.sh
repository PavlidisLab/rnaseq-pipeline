#!/bin/bash

set -e

## Functions
err_report() {
    echo "Error on line $1 in $2"
}
trap 'err_report $LINENO $(basename "$0")' ERR

## Configurations
 
LOCATION="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODES_DIR="$LOCATION""/modes"
mkdir -p "$LOCATION/tmp"
configfile="$LOCATION/common.cfg"
configfile_secured="$LOCATION/tmp/common_"$(uuidgen)".cfg"

cat $configfile > $configfile_secured
printf "\n" >>$configfile_secured
if ! [ -z ${MODES+x} ]; then  
    ## Load additional configuration files
    for MODE in $(echo $MODES | tr ',' '\n'); do
	echo " Loading $MODE"
	cat "$MODES_DIR/"$MODE".cfg" >> $configfile_secured 
	printf "\n" >> $configfile_secured
    done
fi

# Sanitize files
if egrep -q -v '^#|^[^ ]*=[^;]*' "$configfile_secured"; then
  echo "Config file is unclean, cleaning it..." >&2

  # Save output to temporary directory.
  egrep '^#|^[^ ]*=[^;&]*' "$configfile_secured" > "$configfile_secured"".tmp"
  cat "$configfile_secured"".tmp" > "$configfile_secured"
  configfile="$configfile_secured"
  rm "$configfile_secured"".tmp"
fi

source $configfile
>&2 echo "Config file '$configfile' loaded."

