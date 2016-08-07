#!/bin/bash
kvm \
  -name vm \
  -cpu kvm64 \
  -smp 2 \
  -m 512 \
  -drive file=/dev/vg/vm_disk,cache=none,if=virtio,boot=on \
  -drive file=/dev/vg/vm_swap,cache=none,if=virtio \
  -net nic,model=virtio,macaddr=52:54:aa:bb:cc:00 \
  -net tap,ifname=vm.0,script=no \
  -net nic,model=virtio,macaddr=52:54:aa:bb:cc:10 \
  -net tap,ifname=vm.1,script=no \
  -monitor unix:monitor,server,nowait \
  -serial unix:serial,server,nowait \
  -vnc unix:vnc \
  -pidfile pid \
  -daemonize
chgrp kvm {serial,vnc}
chmod g+w {serial,vnc}
