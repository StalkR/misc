#!/bin/bash
# Auto restart aiccu if it fails to ping6.

main() {
  # Usage: $0 [<host to ping>]
  if [[ -z "$DAEMON" ]]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  loop "${1:-ipv6.google.com}"
}

loop() {
  while sleep 10; do
    if ! alive "$1"; then
      logger -t "aiccu" "restart"
      invoke-rc.d aiccu stop
      while pgrep -x aiccu >/dev/null; do
        sleep 1
      done
      invoke-rc.d aiccu start
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
  ping6 -c 1 -w 1 "$1" >/dev/null
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
