#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
source "$BACKUP_DIR/local.cfg"

sed -e "s/{username}/$1/g" -e "s/{password}/$2/g" $SYSTEM_DIR/config/local.cfg.sample > /HDD/local.cfg
