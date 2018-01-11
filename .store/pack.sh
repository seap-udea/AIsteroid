#!/bin/bash
basedir=$(pwd)
pack=$1
if [ "x$pack" == "x" ];then pack="pack";fi

storedir=".store"
confile="pack.conf"

if [ $pack = "pack" ];then
    echo "Packing..."
    rm -r $storedir/*--* &> /dev/null
    for file in $(cat $storedir/$confile |grep -v "#")
    do
	echo -e "\tfile $file..."
	fname=$(basename $file)
	dname=$(dirname $file)
	uname=$(echo $dname |sed -e s/\\//_/)
	sdir="$storedir/$uname--$fname"
	mkdir -p "$sdir"
	cd $sdir
	split -b 20000KB $basedir/$file $fname-
	cd - &> /dev/null
	git add -f "$storedir/$uname--$fname/*"
    done
    git add -f $storedir/*--*
else
    echo "Unpacking..."
    for file in $(cat $storedir/$confile |grep -v "#")
    do
	echo -e "\tUnpacking $file..."
	fname=$(basename $file)
	dname=$(dirname $file)
	uname=$(echo $dname |sed -e s/\\//_/)
	sdir="$storedir/$uname--$fname"
	#echo "cat \"$sdir\"/$fname-* > $dname/$fname"
	cat "$sdir"/$fname-* > $dname/$fname
    done
fi
