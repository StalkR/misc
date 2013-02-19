#!/bin/sh
sudo brctl delif br0 vm.0
sudo brctl delif br1 vm.1

sudo ip link set vm.0 down
sudo ip link set vm.1 down

sleep 1

sudo tunctl -d vm.0
sudo tunctl -d vm.1
