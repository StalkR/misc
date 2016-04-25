#!/bin/bash
# If internet disconnects, reboot modem, wait and reconfigure network.
# Works for UPC Cablecom modem Technicolor TC7200U.

# In bridge mode, modem web interface is at 192.168.100.1
declare -r HOST="192.168.100.1"
declare -r LOGIN="admin"
declare -r PASSWORD="password"
declare -r INTERFACE="eth1"
declare -r INTERNET="8.8.8.8"
declare -r MAILTO="notification@example.com"

main() {
  if [[ -z "$DAEMON" ]]; then
    DAEMON=1 nohup "$0" "$@" >/dev/null 2>&1 &
    exit
  fi
  local out result
  while sleep 10; do
    if alive "$INTERNET"; then
      continue
    fi
    logger -t "modem-reboot" "internet lost, rebooting modem"
    out=$(reboot_modem)
    result=$?
    if [[ $result -eq 0 ]]; then
      logger -t "modem-reboot" "modem reboot successful, internet back up"
      date --rfc-3339=seconds | mail -s "modem rebooted" "$MAILTO"
      continue
    fi
    logger -t "modem-reboot" "modem reboot failed (exit $result): $out"
    { date --rfc-3339=seconds
      echo "$out"
    } | mail -s "modem failed to reboot" "$MAILTO"
    sleep 300
  done
}

alive() {
  local beat
  # maximum 60 times with 10s sleep => 10 mins
  for beat in {1..60}; do
    ping -c 1 -w 1 "$1" >/dev/null && return 0
    sleep 10
  done
  return 1
}

reboot_modem() {
  page=$(curl -si "http://$HOST")
  csrf=$(sed -n 's/.*CSRFValue" value=\([^>]\+\)>.*/\1/p' <<< "$page")
  if [[ ! -n "$csrf" ]]; then
    echo 'login csrf not found'
    return 1
  fi

  page=$(curl -si --data "CSRFValue=$csrf" --data "loginUsername=$LOGIN" \
    --data "loginPassword=$PASSWORD" --data 'logoffUser=1' \
    "http://$HOST/goform/login")
  if ! grep -q "Location: http://$HOST/status/system.asp" <<< "$page"; then
    echo 'login failed'
    return 1
  fi

  page=$(curl -si "http://$HOST/system/backup.asp")
  csrf=$(sed -n 's/.*CSRFValue" value=\([^>]\+\)>.*/\1/p' <<< "$page")
  if [[ ! -n "$csrf" ]]; then
    echo 'backup csrf not found'
    return 1
  fi

  page=$(curl -si --data "CSRFValue=$csrf" --data 'BackupPassword=' \
    --data 'BackupRetypePassword=' --data 'ExportFile=' \
    "http://$HOST/goform/system/backup")
  if ! grep -q "Location: GatewaySettings.bin" <<< "$page"; then
    echo 'backup failed'
    return 1
  fi

  settings=$(mktemp)
  curl -s "http://$HOST/goform/system/GatewaySettings.bin" > "$settings"
  if [[ ! -s "$settings" ]]; then
    rm -f "$settings"
    echo 'download backup failed'
    return 1
  fi

  page=$(curl -si "http://$HOST/system/restore.asp")
  csrf=$(sed -n 's/.*CSRFValueRestore" value=\([^>]\+\)>.*/\1/p' <<< "$page")
  if [[ ! -n "$csrf" ]]; then
    rm -rf "$settings"
    echo 'restore csrf not found'
    return 1
  fi

  page=$(curl -si --form-string "CSRFValueRestore=$csrf" \
    --form-string 'RestorePassword=' --form "ImportFile=@$settings" \
    "http://$HOST/goform/system/restore")
  rm -f "$settings"
  if ! grep -q 'The device has been reset...' <<< "$page"; then
    echo 'reset failed'
    return 1
  fi

  # give some time for modem to shutdown (observed: ~20s)
  local i=0
  while pings "$HOST"; do
    i=$(($i+1))
    if [[ $i -eq 60 ]]; then
      echo 'modem did not shutdown in time'
      return 1
    fi
    sleep 1
  done

  # give some time for modem to start (observed: ~50s)
  i=0
  while ! pings "$HOST"; do
    i=$(($i+1))
    if [[ $i -eq 120 ]]; then
      echo 'modem did not restart in time'
      return 1
    fi
    sleep 1
  done

  # give some time for internet to go back up (observed: ~10s)
  i=0
  while ! pings "$INTERNET"; do
    ifdown "$INTERFACE"
    ifup "$INTERFACE"
    i=$(($i+1))
    if [[ $i -eq 5 ]]; then
      echo 'internet did not come back in time'
      return 1
    fi
    sleep 10
  done
}

pings() {
  local beat
  for beat in {1..5}; do
    ping -c 1 -w 1 "$1" >/dev/null 2>&1 && return 0
  done
  return 1
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
