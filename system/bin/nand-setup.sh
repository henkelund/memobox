#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
cp $SYSTEM_DIR/etc/fstab_nand /etc/fstab
mount /dev/sda1 /HDD
