#!/bin/bash

TODAY=`date +'%Y-%m-%d'`
LOGFILE="/home/niko/projects/wscBot/logs/${TODAY}.log"

git pull
./bottip.py -u -t > ${LOGFILE} 2>&1
