#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"

touch $BACKUP_DIR/index.db
chown www-data:www-data $BACKUP_DIR/index.db

sed -e "s/{username}/$1/g" $SYSTEM_DIR/config/local.cfg.sample > $BACKUP_DIR/local.cfg
chown www-data:www-data $BACKUP_DIR/local.cfg
