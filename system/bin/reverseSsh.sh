#!/bin/bash
OPENPORTS=$(ps auxwww | grep 'ssh -q -fN' | grep -v 'grep' | wc -l)
OPENPORT=$(ps auxwww | grep 'ssh -q -fN' | grep -v 'grep' | awk '{print $2}')

if [ $# -lt 1 ]; then
  echo 1>&2 "Missing remote port"
  exit 2
elif [ $# -gt 2 ]; then
  echo 1>&2 "$0: too many arguments"
  exit 2
fi

echo "first argument $1"
echo "second argument $2"

if [[ "$1" == "KILL" ]]; then 
	if [[ $OPENPORTS -gt 0 ]]; then 
        	ps auxwww | grep 'ssh -q -fN' | grep -v 'grep' | awk '{print $2}' | xargs kill -15
	fi
        exit
fi

# Kill all open connectsion
if [[ "$2" == "KILL" && $OPENPORTS -gt 0 ]]; then 
	ps auxwww | grep 'ssh -q -fN' | grep -v 'grep' | awk '{print $2}' | xargs kill -15
	OPENPORTS=0
fi

if [ $OPENPORTS -eq 0 ]; then
	echo "ssh -q -fN -R $1:localhost:36000 root@regen15050101.backupbox.se"
	ssh -q -fN -R $1:localhost:36000 root@regen15050101.backupbox.se
	#if [ $? -eq 0 ]; then
	#	echo "Port forward to cloud server was established"
	#fi
fi
