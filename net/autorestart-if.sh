#!/bin/bash
# Auto restart interface if it fails to ping.

main() {
  if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <interface> [<host to ping>]"
    exit 1
  fi
  if [[ -z "$DAEMON" ]]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  loop "$1" "${2:-8.8.8.8}"
}

loop() {
  while sleep 10; do
    if ! alive "$1" "$2"; then
      logger -t "network" "restart"
      ifdown "$1"
      sleep 1
      ifup "$1"
      sleep 60
    fi
  done
}

alive() {
  local fail
  for fail in {1..5}; do
    if beat "$1" "$2"; then
      return 0
    fi
  done
  return 1
}

beat() {
  ping -I "$1" -c 1 -w 1 "$2" >/dev/null
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
