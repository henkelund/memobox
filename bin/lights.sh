#!/bin/bash

declare -A lamps
lamps[ORANGE]='/sys/devices/virtual/misc/sun4i-gpio/pin/pd5'
lamps[GREEN]='/sys/devices/virtual/misc/sun4i-gpio/pin/pd6'
signal="0";
blinkfile="/tmp/$1BLINK"
workfile="/tmp/$1WORK"

cleanup()
{
       cleanupwork
       cleanupblink
}


cleanupwork()
{
        rm $workfile > /dev/null 2>&1
}

cleanupblink()
{
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
