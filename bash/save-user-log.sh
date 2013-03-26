#!/bin/bash
# Save user's logs in their home directory.

main() {
  if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <user> [<user> ...]"
    exit 1
  fi
  while [[ -n "$1" ]]; do
    save_user_log "$1"
    shift
  done
}

save_user_log() {
  if [[ ! -d "/home/$1" ]]; then
    echo "Error: no home directory for user $1?" >&2
    return 1
  fi
  local re i
  re="Accepted publickey for $1\|session \(opened\|closed\) for user $1"
  {
    for i in {100..2}; do
      if [[ -f "/var/log/auth.log.$i.gz" ]]; then
        zgrep "$re" < "/var/log/auth.log.$i.gz"
      fi
    done
    if [[ -f /var/log/auth.log.1 ]]; then
      grep "$re" < /var/log/auth.log.1
    fi
    if [[ -f /var/log/auth.log ]]; then
      grep "$re" < /var/log/auth.log
    fi
  } > /home/$1/auth.log
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
