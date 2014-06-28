#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"

sed -e "s/{username}/$1/g" -e "s/{password}/$2/g" $SYSTEM_DIR/config/local.cfg.sample > $BACKUP_DIR/local.cfg
chown www-data:www-data $BACKUP_DIR/local.cfg