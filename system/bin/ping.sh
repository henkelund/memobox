#!/bin/bash
LOGFILE=/var/log/ping.log 
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
pingvalues=`sed '{:q;N;s/\n//g;t q}' /tmp/ping.txt`
source "$BACKUP_DIR/local.cfg"

COMMAND="curl --connect-timeout 5 -s -X GET http://$BOXUSER.backupbox.se/ping?$pingvalues"

echo $COMMAND

#while ! test -f /tmp/stop-my-script
#do
	$BIN_DIR/gatherData.sh &&
	response=`$BIN_DIR/timeout.sh -t 5 $COMMAND`

	if [ "$?" = "0" ] && [ "$response" = "ok" ]; then
		echo "yes"
		$BIN_DIR/lights.sh GREEN ON &
	else
		echo "$response"
		$BIN_DIR/lights.sh GREEN OFF &
	fi

#	sleep 60
#done
