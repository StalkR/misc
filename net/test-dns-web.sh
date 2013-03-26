#!/bin/bash
# Test DNS and Web access, single or loop.

main() {
  if [[ -n "$1" ]]; then
    while sleep "$1"; do
      echo -n "$(date) - "
      run_tests
    done
  else
    run_tests
  fi
}

run_tests() {
  local dns ip rev
  dns=$(dig +short ifconfig.me)
  if [[ -z "$dns" ]]; then
    echo "DNS resolution failed: dig ifconfig.me"
    return 1
  fi
  echo -n "DNS OK - "
  ip=$(curl -4s ifconfig.me/ip)
  if [[ -z "$ip" ]]; then
    echo "Web failed: curl -4 ifconfig.me/ip"
    return 2
  fi
  echo -n "Web OK - "
  echo -n "Current IP: $ip"
  rev=$(dig +short -x "$ip")
  if [[ "${rev:${#rev}-1}" = "." ]]; then
    rev=${rev::${#rev}-1}
  fi
  echo " ($rev)"
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
