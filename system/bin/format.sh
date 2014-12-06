#!/bin/bash

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

# Create root .ssh folder if missing
mkdir /root/.ssh
touch /root/.ssh/known_hosts

# Remove old folders, if they exist
/etc/init.d/uwsgi stop
/etc/init.d/nginx stop
umount /HDD

rm -rf /backupbox/data
rm -rf /HDD
mkdir /HDD

# Fix user permissions and create symlink to hard drive mount point
chown -R www-data:www-data /HDD
chmod 777 -R /HDD
ln -s /HDD /backupbox/data
chown www-data:www-data /backupbox/data
chmod 777 -R /backupbox/data

# Initialize config file. First parameter is username, second parameter is password
/backupbox/system/bin/setup.sh $1

# Create host key and upload it to the server
/backupbox/system/bin/rsa.sh

echo "Start checking for username"
REMOTEUSER=`ssh root@$1.backupbox.se "/backupbox/system/bin/user.sh $1"`
echo "Finished checking for username"

if [[ $REMOTEUSER == *Error* ]]
then
  echo $REMOTEUSER
  echo "User already exists. Please choose another username";
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

# Remove old folders, if they exist
rm -rf /backupbox/data
rm -rf /HDD
mkdir /HDD

# Fix user permissions and create symlink to hard drive mount point
chown -R www-data:www-data /HDD
chmod 777 -R /HDD
ln -s /HDD /backupbox/data
chown www-data:www-data /backupbox/data
chmod 777 -R /backupbox/data

# Try mounting the harddrive
mount /dev/sda1 /HDD

# Create mount folder and give www-data full rights
mkdir /backupbox/data/log
mkdir /backupbox/data/public
mkdir /backupbox/data/cache
mkdir /backupbox/data/devices

# Write serial to file
echo $2 > /backupbox/data/public/serial.txt
touch /backupbox/data/public/_publish

# Restart NGINX and UWSGI
/etc/init.d/uwsgi restart
/etc/init.d/nginx restart

# Generate new config file since we hav formated the hard drive
/backupbox/system/bin/setup.sh $1

# Regenerate rsa keys since we have since formatted the hard drive
/backupbox/system/bin/rsa.sh

# Performing backup
/backupbox/system/bin/backup.sh
