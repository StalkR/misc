#!/bin/bash
# Script maintain /boot on an USB drive so it cannot be tampered with.
# 1) create a grml USB boot device
# 2) edit usb:/boot/syslinux/additional.cfg and add a menu:
#   menu begin other
#     menu title Other
#     label mainmenu
#     menu label ^Back to main menu...
#     menu exit
#     menu separator
#     include /machine/syslinux.cfg
#   menu end
# 3) create a directory for /machine, copy this script and run it from there
# 4) add as many machines as needed: add include, create directory, copy script

main() {
  cd "$(dirname "${BASH_SOURCE[0]}")"
  check
  copy
  syslinux
}

check() {
  local file hostname
  for file in /boot/{config,initrd.img,System.map,vmlinuz}-*; do
    if [[ ! -r "$file" ]]; then
      echo "Error: $file not readable"
      echo "sudo chmod a+r /boot/{config,initrd.img,System.map,vmlinuz}-*"
      exit 1
    fi
  done
  hostname=$(hostname -s)
  if [[ -z "$hostname" ]]; then
    echo "Error: hostname -s is empty"
    exit 1
  fi
}

copy() {
  local file
  rsync -a /boot/{config,initrd.img,System.map,vmlinuz}-* .
  for file in {config,initrd.img,System.map,vmlinuz}-*; do
    if [[ ! -f "/boot/$file" ]]; then
      rm -vf "$file"
    fi
  done
}

syslinux() {
  local hostname path version
  hostname=$(hostname -s)
  path="$(basename "$(pwd -P)")"
  > syslinux.cfg
  for version in vmlinuz-*; do
    version=${version#vmlinuz-*}
    if [[ ! -f "initrd.img-$version" ]]; then
      continue
    fi
    label "$hostname" "$path" "$version" >> syslinux.cfg
  done
}

label() {
  local hostname path version
  hostname=$1
  path=$2
  version=$3
  echo "label $hostname-$version"
  echo "  menu label ^$hostname $version"
  echo "  kernel /$path/vmlinuz-$version"
  echo "  append initrd=/$path/initrd.img-$version" \
    "root=/dev/mapper/vg-root ro quiet splash"
  echo
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
