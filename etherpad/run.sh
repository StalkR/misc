#!/bin.sh
cd /opt/etherpad
mkdir -p log
nohup etherpad-lite/bin/run.sh >> log/run.log 2>&1 &
