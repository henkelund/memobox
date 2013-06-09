#!/bin/bash

###
# This program is intended to setup a working system from scratch including
# installing dependencies, udev rules, crontab entries and what not.
# A modern Debian based GNU/Linux distribution is assumed.
#

printc()  { echo -ne "\e[$2m$1\e[0m"; }
notice()  { printc "$1" "1;34"; }
success() { printc "$1" "0;32"; }
error()   { printc "$1" "0;31"; }
warning() { printc "$1" "1;33"; }

############################
# CHECK FOR INSTALLER DEPS #
############################

echo -n "Checking installer dependencies.. "

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
CAT_NAME="cat"
CAT="$(which ""$CAT_NAME"")"
TEE_NAME="tee"
TEE="$(which ""$TEE_NAME"")"
SUDO=""
if [ $EUID -ne 0 ]
then
    SUDO="$(which sudo)"
    if [ -z "$SUDO" ]
    then
        error "Please install sudo or run as root\n" 1>&2
        exit 1
    fi
fi

for var in PKG_INSTALLER PKG_SEARCHER PKG_MANAGER SED CUT GREP CAT TEE
do
    exe="$(eval echo \$$var)"
    if [ -z "$exe" ]
    then
        name="$(eval echo \$$var\_NAME)"
        echo "The program $name is needed by the installer." 2>&1
        exit 2
    fi
done

success "[OK]\n";

######################
# SET UP DIRECTORIES #
######################

echo -n "Setting up directory structure.. "

BASE_DIR="$(cd ""$(dirname ""$0"")/.."" && pwd)"
BIN_DIR="$BASE_DIR/bin"
DOC_DIR="$BASE_DIR/doc"
ETC_DIR="$BASE_DIR/etc"
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

success "[OK]\n";

########################
# INSTALL DEPENDENCIES #
########################

echo -n "Checking system dependencies.. "

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
    notice "\nPackage $package is required.\n\t"
    $PKG_SEARCHER search "$package" | $GREP --extended-regexp "^$package - "
    echo -en "\tType YES to install it using $PKG_INSTALLER_NAME: "
    read proceed
    echo -en "\n"

    if [ "$proceed" != "YES" ]
    then
        error "Interpreting vague answer as NO.\n"
        error "Exiting\n"
        exit 5
    fi

    $SUDO $PKG_INSTALLER install "$package" \
        || { error "Error installing $package\n"; exit 6; }

    success "$package successfully installed\n"

done

success "[OK]\n";

####################
# SETUP UDEV RULES #
####################

echo -n "Installing udev rules.. "

dispatcher="$BIN_DIR/dispatcher.sh"
template_file="$ETC_DIR/udev/rules.d/99-automount.rules"
template="$($CAT $template_file)"
rule_file="/etc/udev/rules.d/$(basename ""$template_file"")"

if [ -f "$rule_file" ]
then
    rule_backup="$rule_file.$(date +""%s"")"
    warning "\nRule file already exists, backing it up as $rule_backup\n"
    $SUDO mv "$rule_file" "$rule_backup"
fi

echo "${template//#\{DISPATCHER\}/$dispatcher}" \
    | $SUDO $TEE "$rule_file" > /dev/null

$SUDO service udev reload > /dev/null 2>&1
if [ $? -eq 0 ]; then success "[OK]\n"; else error "[FAIL]\n"; fi

#########################
# INSTALLATION COMPLETE #
#########################

success "Installation complete!\n"

exit 0
