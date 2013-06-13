#!/bin/bash
# Auto restart pptp VPN if it fails to ping.

main() {
  if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <vpn name> <interface> [<host to ping>]"
    exit 1
  fi
  if [[ -z "$DAEMON" ]]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  loop "$1" "$2" "${3:-8.8.8.8}"
}

loop() {
  while sleep 10; do
    if ! alive "$2" "$3"; then
      logger -t "$1" "restart"
      poff "$1"
      while ip link list dev "$2" >/dev/null 2>&1; do
        sleep 1
      done
      pon "$1"
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
