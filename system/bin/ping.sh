#!/bin/bash
source "$(dirname ""$0"")/../config/dirs.cfg"
LOGFILE=/var/log/ping.log 
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
PYTHONDIR="$LIB_DIR/python"
EVENTURI="$PYTHONDIR/event/event.py"
PYTHONPATH="$PYTHONPATH:$PYTHONDIR"
$BIN_DIR/gatherData.sh 
PYTHON="$(which python)"

pingvalues=`sed '{:q;N;s/\n//g;t q}' /tmp/ping.txt`
source "$BACKUP_DIR/local.cfg"

export PYTHONPATH

COMMAND="$PYTHON $EVENTURI http://ping.backupbox.se/ping?$pingvalues"

response=`$BIN_DIR/timeout.sh -t 5 $COMMAND`

if [ "$response" = "ok" ]; then
	echo "yes"
	$BIN_DIR/lights.sh GREEN ON &
else
	echo "ERROR:$response"
	echo "DEBUG;$?"
	$BIN_DIR/lights.sh GREEN OFF &
fi
