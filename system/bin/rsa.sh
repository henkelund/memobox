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
echo "Removed RSA Keys"
echo -e "\n\n\n" | ssh-keygen -N ""
echo "Generated new keys"
ssh-keyscan -t rsa,dsa $BOXUSER.backupbox.se 2>&1 | sort -u - /root/.ssh/known_hosts > /root/.ssh/tmp_hosts
echo "Performed keyscan"
cat /root/.ssh/tmp_hosts >> /root/.ssh/known_hosts
echo "Move temporary hosts to known hosts"
sshpass -p 'copiebox' ssh-copy-id -i /root/.ssh/id_rsa.pub root@$BOXUSER.backupbox.se
echo "Upload keys to cloud server"
cp /root/.ssh/id_rsa.pub $BACKUP_DIR/rsa_key
echo "copy public key to Hard drive"
chmod 777 $BACKUP_DIR/rsa_key
echo "Change permissions on rsa key"
