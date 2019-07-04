#!/bin/bash
# Authorized keys command script to enforce sync command.
#
# sync.sh is useful to sync files between two machines, it has various options
# to transfer, mirror with delete, ask before, or use encryption.
# You can use a dedicated ssh key so it can run in the background, then
# restrict usage of that key to sync only using authorized_keys force command
# feature and a little script to only allow rsync with the expected flags and
# arguments, keeping it up to date with sync.sh.
#
# Add it to ~/.ssh/authorized_keys like this:
# command="/home/user/.ssh/sync-check.sh",no-agent-forwarding,no-port-forwarding,no-pty,no-X11-forwarding ssh-xxx [...] sync@host

main() {
  local args
  args=0
  set -- $SSH_ORIGINAL_COMMAND
  [[ "$1" == "rsync" ]] || die "Command not allowed: $1"
  shift
  while [[ -n "$1" ]]; do
    if [[ "$args" == "0" ]] && [[ "${1:0:1}" == "-" ]]; then
      check_flag "$1"
    else
      args=$(($args+1))
      if [[ "$args" -eq 1 ]]; then
        [[ "$1" == "." ]] || die "First argument should be '.': $1"
      else
        check_path "$1"
      fi
    fi
    shift
  done
  exec $SSH_ORIGINAL_COMMAND
}

check_flag() {
  local f
  # We expect exactly these flags, in any order. Adjust as necessary with sync script.
  for f in '--server' '--sender' '-vltrze.iLsfxC' '-vnltrze.iLsfxC' '--delete' '--modify-window=10'; do
    [[ "$1" == "$f" ]] && return
  done
  die "Flag not allowed: $1"
}

check_path() {
  [[ "$1" == *".."* ]] && die "Invalid path: $1"
  # Adjust checks depending on your sync script.
  [[ "${1:0:10}" == '/mnt/sync/' ]] || die "Path not allowed: $1"
  for d in folder{1,2,3}; do
    [[ "${1:10}" == "$d/"* ]] && return
  done
  die "Path not allowed: $1"
}

die() {
  echo "$@" >&2
  exit 1
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi

