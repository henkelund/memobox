#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
source "$BACKUP_DIR/local.cfg"

rm /root/.ssh/id_rsa
rm /root/.ssh/id_rsa.pub
echo -e "\n\n\n" | ssh-keygen -N ""
ssh-copy-id -i /root/.ssh/id_rsa.pub root@$BOXUSER.backupbox.se