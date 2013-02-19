#!/bin/bash
# Auto restart pptp VPN if down.

main() {
  if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <vpn name> <interface>"
    exit 1
  fi
  if [[ -z "$DAEMON" ]]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  loop "$1" "$2"
}

loop() {
  while sleep 60; do
    if ! alive "$2"; then
      poff "$1"
      pon "$1"
    fi
  done
}

alive() {
  local fail
  for fail in {1..5}; do
    if beat "$1"; then
      return 0
    fi
  done
  return 1
}

beat() {
  ping -I "$1" -c 1 8.8.8.8 >/dev/null
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
