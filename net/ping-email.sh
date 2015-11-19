#!/bin/bash
# Monitor a host with ping and alert when it is down or back up.
# Install: @reboot sleep 120; ~/ping-email.sh 8.8.8.8 you@example.com

main() {
  if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <host> <email>"
    exit 1
  fi
  if [[ -z "$DAEMON" ]]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  loop "$1" "$2"
}

loop() {
  local works
  works=1
  while sleep 3600; do
    if alive "$1"; then
      if [[ $works -eq 0 ]]; then
        date --rfc-3339=seconds | mail -s "$1 up" "$2"
        works=1
      fi
    else
      if [[ $works -eq 1 ]]; then
        date --rfc-3339=seconds | mail -s "$1 down" "$2"
        works=0
      fi
    fi
  done
}

alive() {
  local fail
  for fail in {1..6}; do
    if beat "$1"; then
      return 0
    fi
    sleep 10
  done
  return 1
}

beat() {
  ping -c 1 -w 1 "$1" >/dev/null
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
