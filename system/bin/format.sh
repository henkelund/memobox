#!/bin/bash

printf "n\np\n1\n\n\nw\n" | sudo fdisk /dev/sda
mkfs.ext3 /dev/sda1
mount /dev/sda1 /HDD
/etc/init.d/uwsgi restart
chown www-data:www-data /HDD
