#!/bin/bash

set -e

LOCATION="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

configfile="$LOCATION/common.cfg"
configfile_secured="$LOCATION/tmp/common.cfg"

# Sanitize files
if egrep -q -v '^#|^[^ ]*=[^;]*' "$configfile"; then
  echo "Config file is unclean, cleaning it..." >&2

  # Save output to temporary directory.
  egrep '^#|^[^ ]*=[^;&]*'  "$configfile" > "$configfile_secured"
  configfile="$configfile_secured"
fi

source $configfile
echo "Config file '$LOCATION/common.config' loaded."