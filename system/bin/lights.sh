#!/bin/bash

declare -A lamps
lamps[RED]='/sys/class/gpio/gpio41_pd7/value'
lamps[GREEN]='/sys/class/gpio/gpio43_pd5/value'
lamps[BLUE]='/sys/class/gpio/gpio42_pd6/value'
signal="0";
blinkfile="/tmp/$1BLINK"
workfile="/tmp/$1WORK"

init() {
       echo 41 > /sys/class/gpio/export 2>/dev/null
       echo 42 > /sys/class/gpio/export 2>/dev/null
       echo 43 > /sys/class/gpio/export 2>/dev/null
       echo out > /sys/class/gpio/gpio41_pd7/direction 2>/dev/null
       echo out > /sys/class/gpio/gpio42_pd6/direction 2>/dev/null
       echo out > /sys/class/gpio/gpio43_pd5/direction 2>/dev/null
}

cleanup()
{
       init
       cleanupwork
       cleanupblink
}


cleanupwork()
{
       init
       rm $workfile > /dev/null 2>&1
}

cleanupblink()
{
       init
       rm $blinkfile > /dev/null 2>&1
}


# PARSE INPUT DATA
if [ "$2" = "ON" ]; then
  cleanup
	echo 1 > ${lamps[$1]}
elif [ "$2" = "OFF" ]; then
	cleanup
	echo 0 > ${lamps[$1]}
elif [ "$2" = "BLINK" ]; then
	cleanupwork
	cleanupblink
	if [ ! -f $blinkfile ]; then
		touch $blinkfile
		while test -f $blinkfile
		do
			if [ -f $blinkfile ]; then
				echo 1 > ${lamps["$1"]}
			fi
			sleep 0.6
			if [ -f $blinkfile ]; then
				echo 0 > ${lamps["$1"]}
			fi
			sleep 0.6
		done
	fi
elif [ "$2" = "WORK" ]; then
	cleanupblink
	if [ ! -f $workfile ]; then
		touch $workfile
		while test -f $workfile
		do
			echo 1 > ${lamps["$1"]}
			sleep 0.2
			echo 0 > ${lamps["$1"]}
			sleep 0.2
		done
	fi
elif [ "$2" = "STOPBLINK" ]; then
	cleanup
fi
