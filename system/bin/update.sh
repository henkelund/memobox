#!/bin/bash

source /backupbox/system/config/dirs.cfg
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SYSTEM_DIR="$(dirname "$BIN_DIR")"
BACKUP_DIR="$(dirname "$SYSTEM_DIR")/data"
source "$BACKUP_DIR/local.cfg"

if [[ -z "$CHANNEL" ]]; then
	CHANNEL="alpha"
fi

if [[ -z "$AUTOUPDATE" ]]; then
	AUTOUPDATE="true"
fi

if [[ $AUTOUPDATE != "true" ]]; then
	echo "Auto update is disabled for this box. Exiting."
	exit
fi

echo "Auto update from channel: $CHANNEL"

cd $ROOT_DIR
git fetch --all
git reset --hard origin/$CHANNEL
/etc/init.d/uwsgi restart
cd $BIN_DIR

