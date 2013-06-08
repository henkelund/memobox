#!/bin/bash

BACKUP_PATH="$(cd ""$(dirname ""$0"")/../data"" && pwd)"

function upfind
{
    local FIND=$(which find)
    local max_depth=10
    local n=0
    local dir="$1"
    local file="$2"

    while [ -d "$dir" -a $n -lt $max_depth ]
    do
        local path=$("$FIND" -P "$dir" -name "$file" -type f -readable)
        if [ $(echo "$path" | wc -l) -gt 1 ]; then return 1; fi # more than one hit, result ambiguous

        if [ -f "$path" ]
        then
             echo "$path"
             return 0
        fi

        local parent=$(dirname "$dir")
        if [ "$parent" = "$dir" ]; then return 2; fi # root hit
        local dir="$parent"
        local n=$(( $n + 1 ))
    done

    return 3
}

function devpath
{
    path="$DEVPATH"
    if [ -z "$DEVPATH" ]
    then
        path=$(udevadm info --query=path --name="$1" 2>/dev/null)
        if [ "$?" -ne 0 ]; then return 1; fi
    fi
    if [ -d "$path" ]; then echo "$path"; return 0; fi
    if [ -d "/sys$path" ]; then echo "/sys$path"; return 0; fi
    return 2
}

function devprop
{
    path=$(devpath "$1")
    if [ "$?" -ne 0 ]; then return 1; fi
    propfile=$(upfind "$path" "$2")
    if [ "$?" -ne 0 ]; then return 2; fi
    cat "$propfile"
    return 0
}

####
# Usage
#   backupdir /dev/<device>
#
function backupdir
{
    serial=$(devprop "$1" serial)
    if [ "$?" -ne 0 ]; then return 1; fi

    dir="$BACKUP_PATH/$serial"
    if [ ! -d "$dir" ]
    then
        mkdir -p "$dir" > /dev/null
        if [ "$?" -ne 0 ]; then return 2; fi
    fi

    if [ -w "$dir" ]
    then
        for prop in idProduct idVendor manufacturer product serial vendor model
        do
            propfile="$dir/$prop"
            if [ -f "$propfile" ]; then continue; fi
            value=$(devprop "$1" "$prop")
            if [ "$?" -ne 0 ]; then continue; fi
            value=$(echo "$value" | sed 's/^[ \t]*//;s/[ \t]*$//')
            if [ -z "$value" ]; then continue; fi
            echo "$value" > "$propfile" 2>/dev/null
        done
    fi

    echo "$dir"
    return 0
}

###
# Check if device is connected
#
is_connected()
{
    path="$(devpath ""$1"")"
    if [ -z "$path" ]; then echo 0; return 1; fi
    echo 1
    return 0
}
