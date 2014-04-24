#!/bin/bash

source /backupbox/system/config/dirs.cfg

cd $ROOT_DIR
git fetch --all
git reset --hard origin/prototype
cd $BIN_DIR

