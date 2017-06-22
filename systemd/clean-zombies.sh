#!/bin/bash
# Reap zombies by calling waitpid from init
libc=$(awk '$6~"libc-"{print "0x"substr($1,0,index($1,"-"));exit}' /proc/1/maps)
[[ -z "$libc" ]] && exit 1
waitpid=$(readelf -a /lib/x86_64-linux-gnu/libc-*.so | awk '$8~"^waitpid@"{print "0x"$2}')
[[ -z "$waitpid" ]] && exit 1
f=$(mktemp)
ps faux | awk '$0~"[d]efunct"{print "call ('"$libc"'+'"$waitpid"')("$2",0,0)"}' > "$f"
gdb --nx --pid 1 --batch -x "$f"
rm -f "$f"
