#!/bin/bash

declare -A lamps
lamps[RED]='/sys/class/gpio/gpio41_pd7/value'
lamps[GREEN]='/sys/class/gpio/gpio43_pd5/value'
lamps[BLUE]='/sys/class/gpio/gpio42_pd6/value'
signal="0";
blinkfile="/tmp/$1BLINK"
workfile="/tmp/$1WORK"

init() {
       direction=`cat /sys/class/gpio/gpio41_pd7/direction`

       if [ "$direction" != "out" ]; then
       	echo 41 > /sys/class/gpio/export
       	echo 42 > /sys/class/gpio/export
       	echo 43 > /sys/class/gpio/export
       	echo out > /sys/class/gpio/gpio41_pd7/direction
       	echo out > /sys/class/gpio/gpio42_pd6/direction
       	echo out > /sys/class/gpio/gpio43_pd5/direction
       fi
}

if [ -f $lamps["GREEN"] ]; then
	init
fi

stopblink()
{
       rm $blinkfile > /dev/null 2>&1
}


if [ -f ${lamps[$1]} ]; then
	# PARSE INPUT DATA
	if [ "$2" = "ON" ]; then
	  	stopblink
		echo 1 > ${lamps[$1]}
	elif [ "$2" = "OFF" ]; then
		stopblink
		echo 0 > ${lamps[$1]}
	elif [ "$2" = "BLINK" ]; then
		stopblink
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
	elif [ "$2" = "STOPBLINK" ]; then
		stopblink
	fi
fi