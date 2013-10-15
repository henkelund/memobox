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

if [ $EUID -ne 0 ]; then notice "Please run as root\n" 1>&2; exit 1; fi

cd "$(dirname ""$0"")"
source ../config/dirs.cfg

(test -n "$ROOT_DIR" \
    && test -n "$BIN_DIR" \
    && test -n "$LIB_DIR" \
    && test -n "$WWW_DIR" \
    && test -n "$DATA_DIR" \
    && test -n "$DEVICE_DIR" \
    && test -n "$CACHE_DIR" \
    && test -n "$LOG_DIR" \
    && test -n "$CONFIG_DIR" \
        ) || {
        error "The config doesn't define required variables\n" 1>&2; exit 2;
    }

CONFIG="$CONFIG_DIR/chef/config/solo.rb"
JSON="$CONFIG_DIR/chef/config/node.json"
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

# export vars required by the box recipe
export ROOT_DIR
export BIN_DIR
export LIB_DIR
export WWW_DIR
export DATA_DIR
export DEVICE_DIR
export CACHE_DIR
export LOG_DIR

"$CHEF" \
    --config "$CONFIG" \
    --json-attributes "$JSON" \
    --log_level "$LOGLEVEL" \
    --color

if [ $? -eq 0 ]
then
    success "Installation complete!\n"
else
    error "Installation failed to complete.\n" 1>&2; exit 3;
fi

exit 0
