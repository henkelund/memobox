#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
source "$BACKUP_DIR/local.cfg"

if [[ -z "$BOXUSER" ]]; then
	echo "Username not set. Make sure that the local.cfg file is properly configured"
	exit
fi

# Verify that we have a user name
echo "BOXUSER: $BOXUSER"

rm /root/.ssh/id_rsa
rm /root/.ssh/id_rsa.pub
echo -e "\n\n\n" | ssh-keygen -N ""
ssh-keyscan -t rsa,dsa $BOXUSER.backupbox.se 2>&1 | sort -u - /root/.ssh/known_hosts > /root/.ssh/tmp_hosts
cat /root/.ssh/tmp_hosts >> /root/.ssh/known_hosts
sshpass -p 'copiebox' ssh-copy-id -i /root/.ssh/id_rsa.pub root@$BOXUSER.backupbox.se
cp /root/.ssh/id_rsa.pub $BACKUP_DIR/rsa_key
chmod 777 $BACKUP_DIR/rsa_key
