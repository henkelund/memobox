#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
source "$BACKUP_DIR/local.cfg"
DATETIME=$(date "+%Y-%m-%d %H:%M:%S")
PUBLISH_FILE="$BACKUP_DIR/public/_publish"

# Function that dumps database
db_dump() {
	echo "BackupDB"
	#rm /HDD/tmp.db
	/usr/bin/sqlite3 "$BACKUP_DIR/index.db" <<EOF
.timeout 20000
.backup "$BACKUP_DIR/tmp.db"
EOF

}


if [[ $CLOUDBACKUP != "true" ]]; then
	echo "Cloud backup is disabled for this box. Exiting."
	exit
fi

if ps auxwww | grep ".backupbox.se:/backups/" | grep -v grep > /dev/null 2>&1
then
    echo "[$DATETIME] A backup process is already running, exiting.."
else	
	echo "$PUBLISH_FILE"
	if [ "$1" == "LOGBACKUP" ]; then 
		mkdir -p /HDD/public/log
		cp /HDD/log/* /HDD/public/log
		touch /HDD/public/_publish
		echo "Performing log backup"
	fi

	if [ -f $PUBLISH_FILE ]; then		
		echo "Pending publication. Let's upload some files"

		eval $(ssh-agent) # Create agent and environment variables
		ssh-add /backups/dev/rsa_key # Read BOX rsa key

		# Upload public dir
		rsync -avz --progress $BACKUP_DIR/public root@$BOXUSER.backupbox.se:/backups/$BOXUSER

		# Dump the database
		db_dump

		# Upload db and local.cfg
		rsync -avz --progress $BACKUP_DIR/tmp.db root@$BOXUSER.backupbox.se:/backups/$BOXUSER/index.db
		rsync -avz --progress $BACKUP_DIR/local.cfg root@$BOXUSER.backupbox.se:/backups/$BOXUSER

		# Give www-data owner ship to the recently uploaded files
		ssh root@$BOXUSER.backupbox.se "chown -R www-data:www-data  /backups/$BOXUSER"
		
		# Upload thumbnails
		# rsync -avz --progress $BACKUP_DIR/cache root@$BOXUSER.backupbox.se:/backups/$BOXUSER

		# When all is said and done, remove publish_flag
		rm $PUBLISH_FILE
	else
		echo "Nothing to do. Exiting..."
	fi

	if [ "$1" == "FULLBACKUP" ]; then 
		# Create snapshot of database
		db_dump

		# Upload thumbnails
		rsync -avz --progress $BACKUP_DIR/cache root@$BOXUSER.backupbox.se:/backups/$BOXUSER

		# Upload thumbnails
		rsync -avz --progress $BACKUP_DIR/devices root@$BOXUSER.backupbox.se:/backups/$BOXUSER

		# Uplaod DB after content is uploaded
		rsync -avz --progress $BACKUP_DIR/tmp.db root@$BOXUSER.backupbox.se:/backups/$BOXUSER/index.db
	fi	
fi
