#!/bin/bash
# See wifi status with colors
IF=wlan0

# Colors (use echo -e to display)
COLOR_BLACK='\e[0;30m';  COLOR_LBLACK='\e[1;30m';
COLOR_RED='\e[0;31m';    COLOR_LRED='\e[1;31m';
COLOR_GREEN='\e[0;32m';  COLOR_LGREEN='\e[1;32m';
COLOR_YELLOW='\e[0;33m'; COLOR_LYELLOW='\e[1;33m';
COLOR_BLUE='\e[0;34m';   COLOR_LBLUE='\e[1;34m';
COLOR_PURPLE='\e[0;35m'; COLOR_LPURPLE='\e[1;35m';
COLOR_CYAN='\e[0;36m';   COLOR_LCYAN='\e[1;36m';
COLOR_NONE='\e[0m';

/sbin/ifconfig $IF > /dev/null 2>&1
E=$?
if [ $E -ne 0 ]; then
  echo "No such device: $IF - exiting"
  exit 1
fi

while [ 1 ]; do
    SPEED=`/sbin/iwconfig $IF | grep 'Bit Rate:' | cut -d':' -f2 | cut -d' ' -f1`
    if [[ "$SPEED" == [0-9]* ]]; then SPEED=$SPEED' Mb/s'; else SPEED='-------'; fi
    PWR=`/sbin/iwconfig $IF | grep 'Link Quality=' | cut -d= -f2 | cut -d/ -f1`
    if [ "$PWR" == "" ]; then PWR=0; fi
    if [ $PWR -gt 80 ]; then C=$COLOR_GREEN
    else if [ $PWR -gt 60 ]; then C=$COLOR_LBLUE
    else if [ $PWR -gt 40 ]; then C=$COLOR_CYAN
    else if [ $PWR -gt 20 ]; then C=$COLOR_YELLOW
    else if [ $PWR -gt 10 ]; then C=$COLOR_PURPLE
    else C=$COLOR_RED; fi; fi; fi; fi; fi
    echo -e "$C$PWR% $SPEED$COLOR_NONE"
    sleep 1
done
