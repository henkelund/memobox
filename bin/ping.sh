#!/bin/bash
LOGFILE=/var/log/ping.log 

while ! test -f /tmp/stop-my-script
do
  /backupbox/bin/gatherData.sh
	curl -s -X POST -d @/tmp/ping.txt http://ping.backupbox.se/ping.php > /dev/null
	sleep 60
done
