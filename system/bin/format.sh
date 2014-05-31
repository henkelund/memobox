#!/bin/bash
/etc/init.d/uwsgi stop
/etc/init.d/nginx stop
umount /HDD
printf "n\np\n1\n\n\nw\n" | sudo fdisk /dev/sda
mkfs.ext3 /dev/sda1
mkdir /HDD
mount /dev/sda1 /HDD
chown -R www-data:www-data /HDD
mkdir /HDD/log
/etc/init.d/uwsgi restart
/etc/init.d/nginx restart
