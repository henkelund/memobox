#!/bin/bash

# Stop all services if they are running
/etc/init.d/uwsgi stop
/etc/init.d/nginx stop

# Unmount harddrive if it was mounted
umount /HDD

# Repartition the harddrive. All of it
printf "n\np\n1\n\n\nw\n" | sudo fdisk /dev/sda

# Format harddrive
mkfs.ext3 /dev/sda1

# Create mount folder and give ww-data full rights
mkdir /HDD
mkdir /HDD/log
mkdir /HDD/public
mkdir /HDD/cache
mkdir /HDD/devices
chown -R www-data:www-data /HDD
chmod 777 -R /HDD


# Try mounting the harddrive
mount /dev/sda1 /HDD

# Restart NGINX and UWSGI
/etc/init.d/uwsgi restart
/etc/init.d/nginx restart

# Initialize config file. First parameter is username, second parameter is password
/backupbox/system/bin/setup.sh $1 $2

# Create host key and upload it to the server
/backupbox/system/bin/rsa.sh