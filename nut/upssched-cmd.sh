#!/bin/bash
# Dispatch actions on UPS events.

main() {
  local ups timer host to
  ups=${1%%_*}
  timer=${1#*_}
  host=$(hostname)
  to=root

  case "$timer" in
    "fsd")
      date | mail -s "[$ups@$host] Forced shutdown" $to
      shutdown ;;
    "onbatt")
      date | mail -s "[$ups@$host] Power lost, running on battery" $to
      touch /var/run/nut/onbatt ;;
    "onbatt-toolong")
      date | mail -s "[$ups@$host] Too long on battery, forcing shutdown" $to
      touch /var/run/nut/onbatt-toolong
      shutdown ;;
    "online")
      date | mail -s "[$ups@$host] Power is back" $to
      rm -f /var/run/nut/onbatt /var/run/nut/onbatt-toolong ;;
    "lowbatt")
      date | mail -s "[$ups@$host] Low battery" $to ;;
    "commok")
      date | mail -s "[$ups@$host] Communications OK" $to ;;
    "commbad")
      date  | mail -s "[$ups@$host] Communications lost" $to ;;
    "shutdown")
      date | mail -s "[$ups@$host] System being shutdown" $to ;;
    "replbatt")
      date | mail -s "[$ups@$host] Bad battery, replace it" $to ;;
    "nocomm")
      date | mail -s "[$ups@$host] UPS unavailable" $to ;;
    "noparent")
      date | mail -s "[$ups@$host] Shutdown impossible, parent died" $to ;;
    *)
      logger -t upssched-cmd "Unrecognized command: $timer ($1)" ;;
  esac
}

shutdown() {
  ssh -i /etc/nut/shutdown.key root@othermachine halt
  /sbin/upsmon -c fsd
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
