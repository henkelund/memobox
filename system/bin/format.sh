#!/bin/bash

printf "n\np\n1\n\n\nw\n" | sudo fdisk /dev/sda
mkfs.ext3 /dev/sda1
mount /dev/sda1 /HDD
touch /HDD/index.db
chown www-data:www-data /HDD/index.db
/etc/init.d/uwsgi restart
