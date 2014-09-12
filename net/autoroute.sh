#!/bin/bash
# Auto add/delete routes via interface based on ping.

declare -a ROUTES=()

main() {
  if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <interface> <routes...>"
    exit 1
  fi
  if [[ -z "$DAEMON" ]]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  local route
  for route in "${@:2}"; do
    ROUTES+=($route)
  done
  loop "$1"
}

loop() {
  while sleep 10; do
    exists "$1" || continue
    if routing "$1"; then
      if ! alive "$1"; then
        logger -t "autoroute" "route dead, remove"
        del "$1"
      fi
    else
      if alive "$1"; then
        logger -t "autoroute" "route alive, add"
        add "$1"
      fi
    fi
  done
}

exists() {
  ip link show dev "$1" >/dev/null 2>&1
}

routing() {
  [[ -n "$(ip route list "${ROUTES[0]}" dev "$1" 2>/dev/null)" ]]
}

add() {
  local r
  for r in "${ROUTES[@]}"; do
    ip route add "$r" dev "$1"
  done
  ip route flush cache
}

del() {
  local r
  for r in "${ROUTES[@]}"; do
    ip route delete "$r" dev "$1"
  done
  ip route flush cache
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
  # When we beat while route is gone, cannot have rp_filter to 1.
  read x < "/proc/sys/net/ipv4/conf/$1/rp_filter"
  if [[ $x -eq 1 ]]; then
    # 0 and 2 would work, choose 2 in case "all" value is 1
    # because kernel takes max between {all,interface}.
    echo 2 > "/proc/sys/net/ipv4/conf/$1/rp_filter"
  fi
  ping -I "$1" -c 1 -w 1 "${ROUTES[0]}" >/dev/null
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
