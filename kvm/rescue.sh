#!/bin/sh
kvm \
  -name vm \
  -cpu kvm64 \
  -smp 2 \
  -m 512 \
  -boot d \
  -cdrom /home/isos/grml64-full_2012.05.iso \
  -drive file=/dev/vg/vm_boot,cache=none,if=virtio,boot=on \
  -drive file=/dev/vg/vm_rootfs,cache=none,if=virtio \
  -drive file=/dev/vg/vm_swap,cache=none,if=virtio \
  -net nic,model=virtio,macaddr=52:54:aa:bb:cc:00 \
  -net tap,ifname=tc2.0,script=no \
  -net nic,model=virtio,macaddr=52:54:aa:bb:cc:10 \
  -net tap,ifname=tc2.1,script=no \
  -monitor unix:monitor,server,nowait \
  -serial unix:serial,server,nowait \
  -vnc unix:vnc \
  -pidfile pid \
  -daemonize
