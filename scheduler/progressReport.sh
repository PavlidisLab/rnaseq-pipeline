#!/bin/bash

usage ()
{
    echo "Usage:"
    echo " $0 [Options: -h, --help, completed, incomplete]"
    exit -1
}

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    usage
fi

TYPES="download qc process count metadata checkgemma loadgemma purge"
MODE=$1 # Optional

commits=$(find commit/ | grep ".tsv" )
IDS=$(find commit/ | cut -d"_" -f2 | grep ".tsv"| cut -d"." -f1 | sort | uniq)

filter="grep ."
if [ "$MODE" == "completed" ]; then
    filter='egrep -v _'
else 
    if [ "$MODE" == "incomplete" ]; then
	filter='egrep (_|Series)'
    else 
	if [ "$MODE" != "" ]; then
	    echo "Unknown argument $MODE"
	    usage
	    exit -1
	fi
    fi
fi



report () 
{

    printf "PROGRESS REPORT:\n" 
    printf "Series\t$( echo $TYPES | sed 's| |\t|g' )"
    echo
    for ID in $IDS;
    do
	printf "$ID\t"
	for TYPE in $TYPES
	do
	    V=$( echo "$commits" | grep -c "$TYPE""_""$ID" ) 
	    #echo "V for $V"
	    if [ "$V" -gt "0" ]; then
		printf "\tX"
	    else
		printf "\t_"
	    fi
	done
	echo ""
    done
}

report | $filter
