#!/bin/bash
# Script to display remote irssi notifications using ssh.
# Notifications: 2 lines (user, message), see notify.pl.
# Requires: ssh key/agent, notify-send (package libnotify-bin).
# Script goes to background (nohup), use DAEMON=1 to avoid it.

declare -r FILE='~/.irssi/notifications'

main() {
  local TITLE MESSAGE
  if [ $# -lt 1 ]; then
    echo "Usage: $0 <ssh host> [<ssh options> ...]"
    exit 1
  fi
  if [ "$(ssh "$@" 'echo works' 2>/dev/null)" != "works" ]; then
    echo "Error: ssh connection failed (key/agent missing?)."
    exit 1
  fi
  if [ -z "$DAEMON" ]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  while read TITLE; do
    read MESSAGE
    notify-send -i gtk-dialog-info -t 1 -- "$TITLE" "$MESSAGE"
  done < <(ssh "$@" "> $FILE; tail -F $FILE")
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
