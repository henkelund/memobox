#!/bin/bash

printf "n\np\n1\n\n\nw\n" | sudo fdisk /dev/sda
mkfs.ext3 /dev/sda1
