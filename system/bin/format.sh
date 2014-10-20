#!/bin/bash

# Create host key and upload it to the server
/backupbox/system/bin/rsa.sh

REMOTEUSER=`ssh root@nordkvist.backupbox.se "/backupbox/system/bin/user.sh $1"`

if [[ $REMOTEUSER == *Error* ]]
then
  echo $REMOTEUSER
  echo "User already exists. Please choose another username";
  exit
fi

# Check if username was provided
if [ -z "$1" ]
  then
    echo "No username provided"
    echo "usage: ./format.sh username serial"
    exit
fi

# Check if serial no was provided
if [ -z "$2" ]
  then
    echo "No serial number was provided"
    echo "usage: ./format.sh username serial"
    exit
fi

# Stop all services if they are running
/etc/init.d/uwsgi stop
/etc/init.d/nginx stop

# Unmount harddrive if it was mounted
umount /HDD

# Repartition the harddrive. All of it
printf "n\np\n1\n\n\nw\n" | sudo fdisk /dev/sda

# Format harddrive
print f "y\n" | mkfs.ext3 /dev/sda1

# Try mounting the harddrive
mount /dev/sda1 /HDD

# Create mount folder and give ww-data full rights
rm -rf /backupbox/data
mkdir /HDD
mkdir /HDD/log
mkdir /HDD/public
mkdir /HDD/cache
mkdir /HDD/devices

# Write serial to file
echo $2 > /HDD/public/serial.txt
touch /HDD/public/_publish

# Fix user permissions
chown -R www-data:www-data /HDD
chmod 777 -R /HDD
ln -s /HDD /backupbox/data
chown www-data:www-data /backupbox/data
chmod 777 -R /backupbox/data

# Restart NGINX and UWSGI
/etc/init.d/uwsgi restart
/etc/init.d/nginx restart

# Initialize config file. First parameter is username, second parameter is password
/backupbox/system/bin/setup.sh $1

# Performing backup
/backupbox/system/bin/backup.sh
