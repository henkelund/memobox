#!/bin/bash
LOGFILE=/var/log/ping.log 
BACKUPPATH=/backupbox

while ! test -f /tmp/stop-my-script
do
	$BACKUPPATH/bin/gatherData.sh $BACKUPPATH
	curl -s -X POST -d @/tmp/ping.txt http://ping.backupbox.se/ping.php  > /dev/null
	sleep 60
done
