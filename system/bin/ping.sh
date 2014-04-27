#!/bin/bash
LOGFILE=/var/log/ping.log 
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"

COMMAND="curl --connect-timeout 5 -s -X POST -d @/tmp/ping.txt http://www.backupbox.se/index.php/ping"

while ! test -f /tmp/stop-my-script
do
	$BIN_DIR/gatherData.sh $BACKUP_DIR
	response=`$BIN_DIR/timeout.sh -t 5 $COMMAND`

	if [ "$?" = "0" ] && [ "$response" = "ok" ]; then
		echo "yes"
		$BIN_DIR/lights.sh GREEN ON &
	else
		echo "$response"
		cat /tmp/ping.txt
		$BIN_DIR/lights.sh GREEN BLINK &
	fi

	sleep 60
done
