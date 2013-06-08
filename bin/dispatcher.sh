#!/bin/bash

###
# This script interprets udev rules from /etc/udev/rules.d/99-automount.rules,
# prepares arguments for - and runs - the automount.sh script
#
# The { ... } & wrapping around this script is intended to detach the process
# from the caller (udev) to avoid being killed due to timeouts.
#

{
if [ $EUID -ne 0 ]; then echo "Please run as root" 1>&2; exit 1; fi

cd "$(dirname "$0")"

# Define some variables for convenience and readability
CWD="$(pwd)"
PATH="$PATH:$CWD"
LOGFILE="$CWD/../log/automount.log"
TYPE="$1"
LABEL="$2"
DEVPATH="$3"

# Programs w/ default options
AUTOMOUNT="$(which bash) ""$CWD""/automount.sh"
PARTED="$(which parted) --machine --script"
GREP="$(which grep) --extended-regexp"

# Prepare arguments for the automount scripe based on info from our udev rules
ARGS=""
case "$TYPE" in
    "disk")
        # Check if disk is partitioned, exit if so
        $PARTED "$DEVNAME" print | $GREP "^[0-9]+\:" > /dev/null 2>&1
        if [ $? -eq 0 ]; then exit 3; fi
        ;&
    "partition")
        # Unpartitioned disk and partitions are mounted in the same way so we
        # dispatch the events as common type "block"
        TYPE="block"
        ;;
esac

export DEVPATH
$AUTOMOUNT "$TYPE" "$LABEL" "$DEVPATH" $ARGS >> "$LOGFILE" 2>&1
echo "automount.sh returned $?" >> "$LOGFILE"

exit 0
} &
