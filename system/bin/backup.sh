#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
source "$BACKUP_DIR/local.cfg"
echo "$BACKUP_DIR/local.cfg"
echo "$BOXUSER"

# Create backup of main database
echo "BackupDB"
rm /HDD/tmp.db
/usr/bin/sqlite3 /HDD/index.db <<EOF
.timeout 20000
.backup /HDD/tmp.db
EOF

# First copy config file and thumbnails
echo "Backup config file and database"
rsync -avz -e ssh --progress /HDD/tmp.db root@$BOXUSER.backupbox.se:/backups/$BOXUSER
rsync -avz -e ssh --progress /HDD/local.cfg root@$BOXUSER.backupbox.se:/backups/$BOXUSER

echo "Secondly, backup thumbnails"
rsync -avz --progress --exclude index.db /HDD/cache root@$BOXUSER.backupbox.se:/backups/$BOXUSER

# Once thumbnails are uploaded, activate database
echo "Copy DB and fix permissions"
ssh $BOXUSER.backupbox.se "cp /backups/$BOXUSER/tmp.db /backups/$BOXUSER/index.db && chmod 777 /backups/$BOXUSER/index.db && chown www-data:www-data /backups/$BOXUSER/index.db"

# Last, backup all original files
echo "Backup content"
rsync -avz -e ssh --progress --exclude index.db /HDD/devices root@$BOXUSER.backupbox.se:/backups/$BOXUSER