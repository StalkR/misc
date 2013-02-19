#!/bin/sh
[ -z "$USER" ] && USER=`whoami`
sudo tunctl -u $USER -t vm.0
sudo tunctl -u $USER -t vm.1

sudo ip link set vm.0 up
sudo ip link set vm.1 up

sleep 1

sudo brctl addif br0 vm.0
sudo brctl addif br1 vm.1
