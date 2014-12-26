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
  # Do not write directly to user's home directory or a user can prepare
  # a symlink and have the script write somewhere else. Instead, write
  # to temp file and move it.
  file=$(mktemp)
  chmod go+r "$file"
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
  } > "$file"
  # Use -T to treat dest as a normal file, otherwise a user can create a
  # directory "auth.log" (or symlink to a directory) to have us write there.
  mv -T -f "$file" /home/$1/auth.log 2>/dev/null || rm -f "$file"
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
