#!/bin/bash

###
# This script is scheduled by a cron job and dispatches
# indexing work to a python script.
#

if [ $EUID -ne 0 ]; then echo "Please run as root" 1>&2; exit 1; fi

source "$(dirname ""$0"")/../config/dirs.cfg"

(test -n "$LIB_DIR" && test -n "$DATA_DIR") || {
        echo "The config doesn't define required variables" 1>&2; exit 2;
    }

DATABASE="$DATA_DIR/index.db"
PYTHONDIR="$LIB_DIR/python"
INDEXDIR="$PYTHONDIR/indexer"
PYTHONPATH="$PYTHONPATH:$PYTHONDIR"
PYTHON="$(which python)"
DATETIME=$(date "+%Y-%m-%d %H:%M:%S")

if [ "$1" == "RESET" ]; then 
	find "$DATA_DIR/devices"  -name .__indexed__ -exec rm -rf {} \;
	exit 0
fi

if ps auxwww | grep "$INDEXDIR" | grep -v grep > /dev/null 2>&1
then
    echo "[$DATETIME] An index process is already running, exiting.."
else
    export PYTHONPATH
    for indexer in "file" "filetime" "image"
    do
    	echo "$indexer"
        "$PYTHON" "$INDEXDIR/$indexer.py" "$DATABASE" "$DATA_DIR"
    done
fi

