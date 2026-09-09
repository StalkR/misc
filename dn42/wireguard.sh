#!/bin/bash
# Start/stop/restart all wireguard interfaces.

main() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <up|down|restart>"
    exit 1
  fi
  case "$1" in
    up) up ;;
    down) down ;;
    restart) down; up ;;
  esac
}

up() {
  for f in /etc/wireguard/*.conf; do
    file=${f##*/}
    name=${file%.conf}
    wg-quick up "$name"
  done
}

down() {
  for f in /etc/wireguard/*.conf; do
    file=${f##*/}
    name=${file%.conf}
    wg-quick down "$name"
  done
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
