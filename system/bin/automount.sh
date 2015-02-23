#!/bin/bash

###
# This script is called by dispatcher.sh which in turn is triggered by
# udev events. This script handles device mounting and file transfer.
#

if [ $EUID -ne 0 ]; then echo "Please run as root" 1>&2; exit 1; fi

cd "$(dirname ""$0"")"
source ../config/dirs.cfg

(test -n "$BIN_DIR" \
    && test -n "$CONFIG_DIR" \
    && test -n "$DATA_DIR" \
        ) || {
        echo "The config doesn't define required variables" 1>&2; exit 13;
    }

# Define some global variables
PATH="$PATH:$BIN_DIR"
MNTTYPE="$1"
LABEL="$2"
MNTPNT="/media/$LABEL"
COUNT=0
MAX=100
if [ -z $DEVPATH ]; then DEVPATH="$3"; fi

# Programs used in this script
CHKMNT="$(which mountpoint)"
PMOUNT="$(which pmount)"
IFUSE="$(which ifuse)"
IDEVICEPAIR="$(which idevicepair)"
GPHOTOFS="$(which gphotofs)"
MTPFS="$(which go-mtpfs)"
UMOUNT="$(which umount)"
MKDIR="$(which mkdir)"
SLEEP="$(which sleep)"
RSYNC="$(which rsync)"
FIND="$(which find)"
XARGS="$(which xargs)"
CHMOD="$(which chmod)"
MV="$(which mv)"
SED="$(which sed)"

# Check for required executables
for var in CHKMNT PMOUNT IFUSE IDEVICEPAIR UMOUNT MKDIR SLEEP RSYNC FIND XARGS \
           CHMOD MV SED GPHOTOFS
do
    exe="$(eval echo \$$var)"
    if [ -z "$exe" ]
    then
        echo "Fatal: $var is not installed" 2>&1
        exitmanager 11
    fi
done

# Include some helper functions
export DEVPATH
source "$BIN_DIR/synchelper.sh"

messagemanager PENDING $LABEL

# Check if data dir is a mountpoint
#$CHKMNT -q "$DATA_DIR"
#if [ $? -ne 0 ]; then echo "$DATA_DIR is not a mounted volume" 1>&2; exitmanager 2; fi

function is_mounted
{
    $CHKMNT -q "$MNTPNT"
    _is_mounted=$?
    if [ $_is_mounted -eq 0 ]; then echo 1; else echo 0; fi
    return $_is_mounted
}

function _cleanup
{
    echo "[$$] Cleaning up.. Unmounting $MNTPNT"
    $UMOUNT "$MNTPNT" > /dev/null 2>&1
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
    echo "Ready to quit $LABEL"
    exitmanager 0 $LABEL
    echo "Has quit"    
}

# Make sure mount point exists and is free
echo "[$$] $MNTTYPE $LABEL plugged in, initial cleanup:"
_cleanup
if [ $? -ne 0 ]
then
    echo "[$$] Could not complete initial cleanup, exiting" 1>&2
    exitmanager 3
fi
$MKDIR -p "$MNTPNT"
if [ $? -ne 0 ]
then
    echo "[$$] Could not create mount point" 1>&2
    exitmanager 4
fi
trap _cleanup EXIT INT TERM

# Time to do what we came here for
while [ $COUNT -lt $MAX ]
do
    echo "[$$] Mount attempt $(($COUNT + 1))/$MAX"
    case $MNTTYPE in
        "block")
            $PMOUNT --read-only "$LABEL" "$LABEL" > /dev/null
            ;;
        "ifuse")
            $IDEVICEPAIR --udid "$LABEL" unpair #> /dev/null
            $IDEVICEPAIR --udid "$LABEL" validate #> /dev/null
            $IDEVICEPAIR --udid "$LABEL" pair #> /dev/null
			$IFUSE "$MNTPNT" --udid "$LABEL" -o nonempty > /dev/null
            ;;
        "ptp")
            # Udev gives us a filename friendly label: {$BUSNUM}_{$DEVNUM}
            # If we replace the underscore w/ a comma we get a port number
            port="$(echo ""$LABEL"" | $SED --regexp-extended 's/[^0-9]+/,/g')"
            $GPHOTOFS --port=usb:"$port" -o nonempty "$MNTPNT" > /dev/null
            # If the device is busy gphotofs will still claim a successfull
            # mount but trying to ls the mountpoint will reveal the error.
            # This can be due to a file browser conflict and should not be
            # a problem in a headless environment.
            ls "$MNTPNT" > /dev/null 2>&1 || { echo "[$$] I/O Error" 1>&2; _cleanup; }
            ;;
        "mtp")
            echo "Try mounting PTP before MTP"
            port="$(echo ""$LABEL"" | $SED --regexp-extended 's/[^0-9]+/,/g')"
            $GPHOTOFS --port=usb:"$port" -o nonempty "$MNTPNT" > /dev/null
            # a problem in a headless environment.
            ls "$MNTPNT" > /dev/null 2>&1 || { 
            	echo "[$$] I/O Error" 1>&2; _cleanup; 
            	echo "Try mounting MTP instead"

	            if [ -n "$MTPFS" ]
	            then
	                # go-mtpfs cannot find fusermount unless we give it our $PATH
	                export PATH
	                $MTPFS "$MNTPNT" &
					sleep 5
					
					# Check w/ ls cause go-mtpfs can mount an empty fs and still return 0
	                
	                if [ $(ls "$MNTPNT" -1 2>/dev/null | wc -l) -eq 0 ]
	                then
	                    _cleanup
	                fi
	            fi
	
	            #TODO: Handle fall-through for devices that can do both mtp & ptp
            }
            ;;
        *)
            echo "[$$] Unrecognized mount type '$MNTTYPE', exiting" 1>&2
            exitmanager 5
            ;;
    esac

    # Check for successful mount
    if [ $(is_mounted) -eq 1 ]; then break; fi

    $SLEEP 3

    # Check for disconnect
    if [ $(is_connected) -eq 0 ]
    then
        echo "[$$] Device disconnected while trying to mount" 1>&2
        exitmanager 12
    fi

    # Some other instance of this script could potentially
    # snatch the mount point while we were sleeping
#    if [ $(is_mounted) -eq 0 ]
#    then
#        echo "Some other process has already mounted $MNTPNT, exit w/o cleanup" 1>&2
#        trap - EXIT INT TERM
#        exitmanager 6
#    fi

    COUNT=$(($COUNT + 1))
done

# Check if the loop was able to mount
if [ $(is_mounted) -ne 1 ]
then
    echo "[$$] Failed to mount after $COUNT attempts" 1>&2
    exitmanager 7
fi

# Prepare for file transfer
SRC="$MNTPNT"
DEST="$(backupdir "$LABEL")"
if [ ! -d "$DEST" -o ! -w "$DEST" ]
then
    echo "$DEST is not a writeable directory, exiting" 1>&2
    exitmanager 8
fi
TMPDEST="$DEST/tmp"
$MKDIR -p "$TMPDEST"

# Uncomment to not rely on rsync filters and only copy camera files instead
#if [ -d "$SRC/DCIM" ]; then SRC="$SRC/DCIM"; fi
#if [ -d "$SRC/Phone/DCIM" ]; then SRC="$SRC/Phone/DCIM"; fi
DCIMDIR="$(finddcim $MNTPNT)"
if [ -d "$DCIMDIR/DCIM" ]; then SRC="$DCIMDIR/DCIM"; fi
echo "$SRC"

echo "[$$] DEBUG ($SRC)" 1>&2

messagemanager WORKING  $LABEL

echo "[$$] Starting transfer from $SRC to $TMPDEST"
$RSYNC                                               \
    --archive                                        \
    --no-owner                                       \
    --no-group                                       \
    --quiet                                          \
    --prune-empty-dirs                               \
    --filter="merge $CONFIG_DIR/rsync.hidden.filter" \
    "$SRC/" "$TMPDEST/"                              \
    2>/dev/null
err=$?
if [ $err -eq 23 ]
then
    echo "[$$] Transfer had non-fatal errors" 2>&1
elif [ $err -ne 0 ]
then
    echo "[$$] Device disconnected during transfer (1) [$err]" 2>&1
    exitmanager 9
fi
# check if device looks disconnected
SRC_LS_CNT=$(ls -1 "$MNTPNT" 2>/dev/null | wc -l)
if [ $(is_connected) -eq 0 -o $SRC_LS_CNT -eq 0 ]
then
    echo "[$$] Device disconnected during transfer (2)" 1>&2
    exitmanager 10
fi

$FIND "$TMPDEST"    \
    -type f -print0 \
    | $XARGS        \
        -0 $CHMOD 644 2>/dev/null

$FIND "$TMPDEST"    \
    -type d -print0 \
    | $XARGS        \
        -0 $CHMOD 755 2>/dev/null

FINALDEST="$DEST/backups/$(date +"%Y/%m/%d")"
$MKDIR -p "$FINALDEST"
$MV "$TMPDEST" "$FINALDEST/$(date +"%H%M%S")"

trap - EXIT INT TERM
_cleanup

exitmanager 0
