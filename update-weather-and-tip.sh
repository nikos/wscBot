#!/bin/bash

TODAY=`date +'%Y-%m-%d'`
LOGFILE="logs/${TODAY}.log"

git pull
./bottip.py -u -t > ${LOGFILE} 2>&1
