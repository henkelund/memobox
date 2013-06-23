#!/bin/bash

freespace () {
        mount_point="$1"
        used_space=0
        mount_point=${1:-"/tmp"}
        threshold=${2:-10}
         
        used_space=`df -k $mount_point | grep % | awk {'print $5'} | sed 's/%//g'`
        used_space=`echo "$used_space" | sed -n 2p`
        
        available_space=`df -kH $mount_point | grep % | awk {'print $2'} | sed 's/%//g'`
        available_space=`echo "$available_space" | sed -n 2p`
        
        echo "available_space=$available_space&"
        echo "free_space=`expr 100 - $used_space`%&"
}

gatherdevices () {
  devices=`find -L $1/data -maxdepth 2 -name manufacturer -printf '%h;'`
	arrIN=(${devices//;/ })
	declare -a DEVICES
	
	c=0
	for i in "${arrIN[@]}"
	do
	        path=(${i//// })
	        #echo ${path[2]}
	        manufacturer=`cat $i/manufacturer`
	        product=`cat $i/product`
	        model=`cat $i/model`
		size=`du -sch $i 2>/dev/null | sed -n '$p'`
		size=(${size//\t/ })
		size=${size[0]}
	        DEVICES["$c"]="${path[2]};$manufacturer;$product;$model;$size"
	        let c=c+1
	done
	
	tLen=${#DEVICES[@]}
	
	echo numdevices=$tLen&
	for (( i=0; i<${tLen}; i++ ));
	do
	  echo "device$i=${DEVICES[$i]}&"
	done
}
