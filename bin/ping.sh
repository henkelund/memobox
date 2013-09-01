#!/bin/bash
LOGFILE=/var/log/ping.log 
BACKUPPATH=/backupbox
COMMAND="curl --connect-timeout 5 -s -X POST -d @/tmp/ping.txt http://www.backupbox.se/index.php/ping"

while ! test -f /tmp/stop-my-script
do
	$BACKUPPATH/bin/gatherData.sh $BACKUPPATH
	response=`$BACKUPPATH/bin/timeout.sh -t 5 $COMMAND`

	if [ "$?" = "0" ] && [ "$response" = "ok" ]; then
		echo "yes"
		$BACKUPPATH/bin/lights.sh GREEN ON &
	else
		echo "$response"
		cat /tmp/ping.txt
		$BACKUPPATH/bin/lights.sh GREEN BLINK &
	fi

	sleep 1
done
