#!/bin/bash
INFOFILE=/tmp/info.txt
PINGFILE=/tmp/ping.txt

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
source "$BACKUP_DIR/local.cfg" 


# Load helper functions for getting system data
source $BIN_DIR/pinghelper.sh
# Load the public IP of the memorybox
pip=$(curl --connect-timeout 5 -s -X GET http://$BOXUSER.backupbox.se/public_ip)
echo "Public IP Address: $pip" > $INFOFILE
# Load the local IP on the router
lip=$(/sbin/ifconfig eth0 | /bin/grep 'inet addr:' | /usr/bin/cut -d: -f2 | /usr/bin/awk '{ print $1}')
echo "Local IP Address: $lip" >> $INFOFILE
#Load Unique ID of backup hard drive
uuid=`/sbin/blkid -s UUID -o value /dev/sda1`
echo "Unique Device ID: $uuid" >> $INFOFILE
# Calculate free and total space of the backup drive
freespace human $BACKUP_DIR >> $INFOFILE

ver=$(cd /backupbox && git log -1 --format=%cd .)
echo "Current Software Version: $ver" >> $INFOFILE
# Load information of all backed up devices
#gatherdevices $1>> $INFOFILE
echo " " >> $INFOFILE
echo "All Connected Devices" >> $INFOFILE
/usr/bin/sqlite3  -init <(echo .timeout 5000) -line $BACKUP_DIR/index.db "select * from device" 2>/dev/null >> $INFOFILE

## Start writing the file used for pingin central server ##

# Load the public IP of the memorybox
echo "public_ip=$pip&" > $PINGFILE
# Load the local IP on the router
echo "local_ip=$lip&" >> $PINGFILE
#Load Unique ID of backup hard drive
echo "uuid=$uuid&" >> $PINGFILE
#Append username to 
echo "username=$BOXUSER&" >> $PINGFILE
devicecount=`find $BACKUP_DIR/devices -type f | wc -l`
echo "devicecount=$devicecount&" >> $PINGFILE
cachecount=`find $BACKUP_DIR/cache -type f | wc -l`
echo "cachecount=$cachecount&" >> $PINGFILE
echo "software=$ver&" >> $PINGFILE
freespace computer $BACKUP_DIR >> $PINGFILE
