#!/bin/bash
# Auto restart aiccu if IPv6 is down.

main() {
  if [[ -z "$DAEMON" ]]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  loop
}

loop() {
  while sleep 10; do
    if ! alive; then
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
    if beat; then
      return 0
    fi
  done
  return 1
}

beat() {
  ping6 -c 1 -w 1 ipv6.google.com >/dev/null
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
