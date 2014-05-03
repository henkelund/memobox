#!/bin/bash

# Create backup of main database
/usr/bin/sqlite3 /HDD/index.db <<EOF
.timeout 20000
.backup /HDD/tmp.db
EOF

# Backup all content
rsync -avz --exclude index.db /HDD/ nordkvist.backupbox.se:/HDD/

# Copy database
rsync -avz /HDD/tmp.db nordkvist.backupbox.se:/HDD/index.db

# Restart uwsgi on remote server in order to reload database
ssh nordkvist.backupbox.se '/etc/init.d/uwsgi restart'

#done
