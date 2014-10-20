#!/bin/bash

USERDIR=/backups/$1

echo "DIR: $USERDIR"

if [ -d "$USERDIR" ]; then
  echo "Error: User already exists. Exiting"
  exit -1
fi

mkdir $USERDIR
touch $USERDIR/ping.db
chown www-data:www-data $USERDIR
chmod -R 777 $USERDIR
