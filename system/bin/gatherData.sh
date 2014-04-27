#!/bin/bash

INFOFILE=/tmp/info.txt
PINGFILE=/tmp/ping.txt

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load helper functions for getting system data
source $BIN_DIR/pinghelper.sh

# Load the public IP of the memorybox
pip=$(curl -Ls http://ping.backupbox.se/public_ip.php)
echo "Public IP Address: $pip" > $INFOFILE

# Load the local IP on the router
lip=$(ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}')
echo "Local IP Address: $lip" >> $INFOFILE

#Load Unique ID of backup hard drive
uuid=`blkid -s UUID -o value /dev/sda1`
echo "Unique Device ID: $uuid" >> $INFOFILE

# Calculate free and total space of the backup drive
freespace human /HDD >> $INFOFILE

ver=$(cd /backupbox && git log -1 --format=%cd .)
echo "Current Software Version: $ver" >> $INFOFILE

# Load information of all backed up devices
#gatherdevices $1>> $INFOFILE
echo " " >> $INFOFILE
echo "All Connected Devices" >> $INFOFILE
/usr/bin/sqlite3  -init <(echo .timeout 5000) -line /HDD/index.db "select * from device" >> $INFOFILE


## Start writing the file used for pingin central server ##

# Load the public IP of the memorybox
pip=$(curl -Ls http://ping.backupbox.se/public_ip.php)
echo "public_ip=$pip&" > $PINGFILE

# Load the local IP on the router
lip=$(ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}')
echo "local_ip=$lip&" >> $PINGFILE

#Load Unique ID of backup hard drive
uuid=`blkid -s UUID -o value /dev/sda1`
echo "uuid=$uuid&" >> $PINGFILE

freespace computer /HDD >> $PINGFILE