#!/bin/bash

###
# This script is called by dispatcher.sh which in turn is triggered by
# udev events. This script handles device mounting and file transfer.
#

if [ $EUID -ne 0 ]; then echo "Please run as root" 1>&2; exit 1; fi

cd "$(dirname "$0")"

# Define some global variables
CWD="$(pwd)"
PATH="$PATH:$CWD"
DATADIR="$(cd ""$CWD/../data"" && pwd)"
MNTTYPE="$1"
LABEL="$2"
MNTPNT="/media/$LABEL"
COUNT=0
MAX=100

# Programs used in this script
CHKMNT="$(which mountpoint)"
PMOUNT="$(which pmount) --read-only"
IFUSE="$(which ifuse)"
IDEVICEPAIR="$(which idevicepair)"
UMOUNT="$(which umount)"
MKDIR="$(which mkdir) -p"
SLEEP="$(which sleep) 3"
RSYNC="$(which rsync)"
FIND="$(which find)"
XARGS="$(which xargs)"
CHMOD="$(which chmod)"
MV="$(which mv)"

# Include some helper functions
source "$CWD/synchelper.sh"

# Check if data dir is a mountpoint
$CHKMNT -q "$DATADIR"
if [ $? -ne 0 ]; then echo "$DATADIR is not a mounted volume" 1>&2; exit 2; fi

function is_mounted
{
    $CHKMNT -q "$MNTPNT"
    _is_mounted=$?
    if [ $_is_mounted -eq 0 ]; then echo 1; else echo 0; fi
    return $_is_mounted
}

function _cleanup
{
    echo "Cleaning up"
    while [ $(is_mounted) -eq 1 ];
    do
        echo -e "\tUnmounting $MNTPNT"
        $UMOUNT "$MNTPNT" > /dev/null 2>&1
        err=$?
	if [ $err -ne 0 ]
        then
            echo -e "\tCould not unmount $MNTPNT ($err)" 1>&2
            return 1
        fi
    done
    return 0
}

# Make sure mount point exists and is free
echo "$MNTTYPE $LABEL plugged in, initial cleanup:"
_cleanup
if [ $? -ne 0 ]
then
    echo "Could not complete initial cleanup, exiting" 1>&2
    exit 3
fi
$MKDIR "$MNTPNT"
if [ $? -ne 0 ]
then
    echo "Could not create mount point" 1>&2
    exit 4
fi
trap _cleanup EXIT INT TERM

# Time to do what we came here for
while [ $COUNT -lt $MAX ]
do
    echo "Mount attempt $(($COUNT + 1))/$MAX"
    case $MNTTYPE in
        "block")
            $PMOUNT "$LABEL" "$LABEL"
            ;;
        "ifuse")
            $IDEVICEPAIR --uuid "$LABEL" unpair      \
                && $IDEVICEPAIR --uuid "$LABEL" pair \
                && $IFUSE "$MNTPNT" --uuid "$LABEL" -o nonempty
            ;;
        "ptp")
            wait
            ;&
        *)
            echo "Unrecognized mount type '$MNTTYPE', exiting" 1>&2
            exit 5
            ;;
    esac
    if [ $(is_mounted) -eq 1 ]; then break; fi
    $SLEEP
    # Some other instance of this script could potentially
    # snatch the mount point while we were sleeping
#    if [ $(is_mounted) -eq 0 ]
#    then
#        echo "Some other process has already mounted $MNTPNT, exit w/o cleanup" 1>&2
#        trap - EXIT INT TERM
#        exit 6
#    fi
    COUNT=$(($COUNT + 1))
done

# Check if the loop was able to mount
if [ $(is_mounted) -ne 1 ]
then
    echo "Failed to mount after $COUNT attempts" 1>&2
    exit 7
fi

# Prepare for file transfer
SRC="$MNTPNT"
DEST="$(backupdir "$LABEL")"
if [ ! -d "$DEST" -o ! -w "$DEST" ]
then
    echo "$DEST is not a writeable directory, exiting" 1>&2
    exit 8
fi
TMPDEST="$DEST/tmp"
$MKDIR "$TMPDEST"

# Uncomment to not rely on rsync filters and only copy camera files instead
#if [ -d "$SRC/DCIM" ]; then SRC="$SRC/DCIM"; fi

echo "Starting transfer from $SRC to $TMPDEST"
$RSYNC                                               \
    --archive                                        \
    --no-owner                                       \
    --no-group                                       \
    --quiet                                          \
    --prune-empty-dirs                               \
    --filter="merge $CWD/config/rsync.hidden.filter" \
    "$SRC/" "$TMPDEST/"                              \
    2>/dev/null
err=$?
if [ $err -eq 23 ]
then
    echo "Transfer had non-fatal errors" 2>&1
elif [ $err -ne 0 ]
then
    echo "Device disconnected during transfer (1)" 2>&1
    exit 9
fi
# check if source folder is empty
SRC_LS_CNT=$(ls -1 "$MNTPNT" 2>/dev/null | wc -l)
if [ $SRC_LS_CNT -eq 0 ]
then
    echo "Device disconnected during transfer (2)" 1>&2
    exit 10
fi

$FIND "$TMPDEST"    \
    -type f -print0 \
    | $XARGS        \
        -0 $CHMOD 644

$FIND "$TMPDEST"    \
    -type d -print0 \
    | $XARGS        \
        -0 $CHMOD 755

FINALDEST="$DEST/$(date +"%Y/%m/%d")"
$MKDIR "$FINALDEST"
$MV "$TMPDEST" "$FINALDEST/$(date +"%H%M%S")"

trap - EXIT INT TERM
_cleanup

exit 0
