#!/bin/bash

###
# This program is intended to setup a working system from scratch including
# installing dependencies, udev rules, crontab entries and what not.
# A modern Debian based GNU/Linux distribution is assumed.
#

if [ $EUID -ne 0 ]; then echo "Please run as root" 1>&2; exit 1; fi

printc()  { echo -ne "\e[$2m$1\e[0m"; }
notice()  { printc "$1" "1;34"; }
success() { printc "$1" "0;32"; }
error()   { printc "$1" "0;31"; }
warning() { printc "$1" "1;33"; }

cd "$(dirname "$0")"
CWD="$(pwd)"
BOX_DIR="$(cd .. && pwd)"
CONFIG="$CWD/chef/config/solo.rb"
JSON="$CWD/chef/config/node.json"
LOGLEVEL="warn" # debug, info, warn, error, fatal
CHEF="$(which chef-solo)"

if [ -z "$CHEF" ]
then
    notice "Installing chef dependencies..\n"
    apt-get install build-essential ruby-dev
    notice "Installing chef..\n"
    gem install chef --no-ri --no-rdoc
    CHEF="$(which chef-solo)"
fi

notice "Running setup recipes..\n"
export BOX_DIR
"$CHEF" \
    --config "$CONFIG" \
    --json-attributes "$JSON" \
    --log_level "$LOGLEVEL" \
    --color

notice "Installation complete!\n"
exit 0

