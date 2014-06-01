#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
source "$BACKUP_DIR/local.cfg"

# Create backup of main database
rm /HDD/tmp.db
/usr/bin/sqlite3 /HDD/index.db <<EOF
.timeout 20000
.backup /HDD/tmp.db
EOF

# Backup all content
rdiff-backup --force --exclude /HDD/index.db /HDD/ root@$BOXUSER.backupbox.se::/HDD/

# Copy database
ssh $BOXUSER.backupbox.se 'cp /HDD/tmp.db /HDD/index.db && chmod 777 /HDD/index.db'

# Restart uwsgi on remote server in order to reload database
ssh $BOXUSER.backupbox.se '/etc/init.d/uwsgi restart'

#done
