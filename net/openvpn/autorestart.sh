#!/bin/bash
# Auto restart OpenVPN if down.

main() {
  if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <interface>"
    exit 1
  fi
  if [[ -z "$DAEMON" ]]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  loop "$1"
}

loop() {
  while sleep 10; do
    if ! alive "$1"; then
      logger -t "openvpn" "restart"
      invoke-rc.d openvpn stop
      while ip link list dev "$1" >/dev/null 2>&1; do
        sleep 1
      done
      invoke-rc.d openvpn start
      sleep 60
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
  ping -I "$1" -c 1 -w 1 8.8.8.8 >/dev/null
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
