#!/bin/bash

set -e

## Traps

## Functions
err_report() {
	#echo "Last command run was ["!:0"] with arguments ["!:*"]"
    echo "[ERROR] Error on line $1 in $2"
	PROGRAM=$(basename $0)

	if [ -z ${CURRENTGSE+x} ]; then 
		CURRENTGSE="CurrentGSE" ; 
	fi

	echo "[ERROR] See logs at LOGS/CURRENTGSE/PROGRAM{.err,.log} or LOGS/PROGRAM/"
    exit 123
}
# trap 'err_report $LINENO $(basename "$0")' ERR

function zhead () { 
    # Get the header of a .gz file
    zcat $1 | head -n1 ; 
}; 
export -f zhead;

shellcheck_suppress () {
    # Suppress a shellcheck warning by adding something harmless to then end of a pipe
    tee;
};
export -f shellcheck_suppress

## ShellCheck specific
suppress_SC2001 () {
    # Suppress the echo|sed replacement warning for cases where native bash substitutions isn't enough.
    shellcheck_suppress ;
};
export -f suppress_SC2001


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

### Machine specific ###
contains() {
    [[ " $1 " =~ " $2 " ]] && echo "yes" || echo 0
}

# HOSTFIRSTNAME=$(echo $HOSTNAME | cut -f1 -d".")
#$(contains "server1 server2 server3 "  "$HOSTFIRSTNAME")
isContained="yes" 

if [ "$isContained" == "yes" ]; then
    if [ -z ${VENV+x} ]; then
	echo "No virtualenv."
    else
	echo "Virtualenv:" $VENV
	set +u
	source $VENV
	set -u
    fi
fi


