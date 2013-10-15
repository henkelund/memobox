#!/bin/bash

printf "n\np\n1\n2048\n927934509\nw\n" | sudo fdisk /dev/sda
mkfs.ext3 /dev/sda1
