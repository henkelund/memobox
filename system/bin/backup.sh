#!/bin/bash

# Create backup of main database
rm /HDD/tmp.db
/usr/bin/sqlite3 /HDD/index.db <<EOF
.timeout 20000
.backup /HDD/tmp.db
EOF

# Backup all content
rdiff-backup --force --exclude /HDD/index.db /HDD/ root@nordkvist.backupbox.se::/HDD/

# Copy database
ssh nordkvist.backupbox.se 'cp /HDD/tmp.db /HDD/index.db && chmod 777 /HDD/index.db'

# Restart uwsgi on remote server in order to reload database
ssh nordkvist.backupbox.se '/etc/init.d/uwsgi restart'

#done
