#!/bin/bash

###
# This program is intended to setup a working system from scratch including
# installing dependencies, udev rules, crontab entries and what not.
# A modern Debian based GNU/Linux distribution is assumed.
#

############################
# CHECK FOR INSTALLER DEPS #
############################

echo "Checking installer dependencies"

PKG_INSTALLER_NAME="apt-get"
PKG_INSTALLER="$(which ""$PKG_INSTALLER_NAME"")"
PKG_SEARCHER_NAME="apt-cache"
PKG_SEARCHER="$(which ""$PKG_SEARCHER_NAME"")"
PKG_MANAGER_NAME="dpkg"
PKG_MANAGER="$(which ""$PKG_MANAGER_NAME"")"
SED_NAME="sed"
SED="$(which ""$SED_NAME"")"
CUT_NAME="cut"
CUT="$(which ""$CUT_NAME"")"
GREP_NAME="grep"
GREP="$(which ""$GREP_NAME"")"
SUDO=""
if [ $EUID -ne 0 ]
then
    SUDO="$(which sudo)"
    if [ -z "$SUDO" ]
    then
        echo "Please install sudo or run as root" 1>&2
        exit 1
    fi
fi

for var in PKG_INSTALLER PKG_SEARCHER PKG_MANAGER SED CUT GREP
do
    exe="$(eval echo \$$var)"
    if [ -z "$exe" ]
    then
        name="$(eval echo \$$var\_NAME)"
        echo "The program $name is needed by the installer." 2>&1
        exit 2
    fi
done

######################
# SET UP DIRECTORIES #
######################

echo "Setting up directory structure"

BASE_DIR="$(cd ""$(dirname ""$0"")/.."" && pwd)"
DOC_DIR="$BASE_DIR/doc"
LOG_DIR="$BASE_DIR/log"
DATA_DIR="$BASE_DIR/data"

if [ ! -d "$BASE_DIR" -o ! -w "$BASE_DIR" ]
then
    echo "$BASE_DIR is not a writable directory" 1>&2
    exit 3
fi

for dir in LOG_DIR DATA_DIR
do
    path="$(eval echo \$$dir)"
    if [ ! -d "$path" ]
    then
        mkdir -p "$path"
    fi
done

########################
# INSTALL DEPENDENCIES #
########################

echo "Checking system dependencies"

DEPS_FILE="$DOC_DIR/dependencies"
NORM_WS="s/[ \t]+/ /"
INST_PKGS=$(
    $PKG_MANAGER --get-selections | $SED --regexp-extended "$NORM_WS")
MISSING_PKGS=""

while read line
do
    if [[ "$line" =~ ^# ]] ; then continue; fi # comment line
    line=$(echo "$line" | $SED --regexp-extended "$NORM_WS")
    program=$(echo "$line" | $CUT --delimiter=' ' --fields=1)
    package=$(echo "$line" | $CUT --only-delimited --delimiter=' ' --fields=2)
    if [ -z "$program" ]; then continue; fi # empty / invalid line
    if [ -n "$(which ""$program"")" ]; then continue; fi # already installed
    if [ -z "$package" ]; then package="$program"; fi

    echo "$INST_PKGS" | \
        $GREP --extended-regexp "^$package install\$" > /dev/null \
        && {
            echo "$program not found but pkg $package is already installed" 1>&2
            echo "please resolve this manually" 1>&2
            exit 4
        }

    MISSING_PKGS="$MISSING_PKGS "$(echo "$package" | $SED --regexp-extended 's/[ \t]+//')

done < "$DEPS_FILE"

for package in $MISSING_PKGS
do
    echo -en "Package $package is required.\n\t"
    $PKG_SEARCHER search "$package" | $GREP --extended-regexp "^$package - "
    echo -en "\tType YES to install it using $PKG_INSTALLER_NAME: "
    read proceed
    echo -en "\n"

    if [ "$proceed" != "YES" ]
    then
        echo "Interpreting vague answer as NO."
        echo "Exiting.."
        exit 5
    fi

    $SUDO $PKG_INSTALLER install "$package"

done

####################
# SETUP UDEV RULES #
####################

#TODO

#########################
# INSTALLATION COMPLETE #
#########################

echo "Installation complete"

exit 0
