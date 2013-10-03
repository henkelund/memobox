#!/bin/bash

###
# This script is scheduled by a cron job and dispatches
# indexing work to a python script.
#

if [ $EUID -ne 0 ]; then echo "Please run as root" 1>&2; exit 1; fi

cd "$(dirname "$0")/.."
CWD="$(pwd)"
DATADIR="$CWD/data"
DATABASE="$DATADIR/index.db"
PYTHONDIR="$CWD/lib/python"
INDEXDIR="$PYTHONDIR/indexer"
PYTHONPATH="$PYTHONPATH:$PYTHONDIR"
PYTHON="$(which python)"
DATETIME=$(date "+%Y-%m-%d %H:%M:%S")

if ps auxwww | grep "$INDEXDIR" | grep -v grep > /dev/null 2>&1
then
    echo "[$DATETIME] An index process is already running, exiting.."
else
    export PYTHONPATH
    for indexer in "file" "filetime"
    do
        "$PYTHON" "$INDEXDIR/$indexer.py" "$DATABASE" "$DATADIR" &
    done
fi

