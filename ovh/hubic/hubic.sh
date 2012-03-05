#!/bin/bash
# Get CloudNAS credentials for OVH HubiC
# Then use davfs2: mount -t davfs <url> <point> and enter credentials
# -- StalkR

BASEURL="https://ws.ovh.com/cloudnas/r0/ws.dispatcher"
USERAGENT="User-Agent: hubiC/1.0.9 (Windows NT 5.1; en_US)"

main() {
  local SESSION NAS_URL CREDENTIALS
  if [ $# -lt 2 ]; then
    echo "Usage: $0 <user> <pass>"
    exit 1
  fi
  SESSION=$(get_session "$1" "$2")
  NAS_URL=$(get_nas "$SESSION")
  CREDENTIALS=$(get_credentials "$SESSION")
  echo "NAS URL: $NAS_URL"
  echo "Credentials: $CREDENTIALS"
}

error() {
  echo "Error: $@" >&2
  exit 1
}

get_session() { # args: user pass
  local PARAMS JS SESSION
  PARAMS='{"email":"'$1'","password":"'$2'"}'
  JS=$(curl -s -A "$USERAGENT" -d "session=" \
         --data-urlencode "params=$PARAMS" \
         "$BASEURL/nasLogin")
  SESSION=$(echo "$JS" | grep -o "paas/cloudnas-[0-9a-f]\{32\}")
  [ -n "$SESSION" ] || error "obtaining session"
  echo "$SESSION"
}

get_nas() { # args: session
  local JS URL
  JS=$(curl -s -A "$USERAGENT" -d "session=$1" \
         "$BASEURL/getNas")
  echo "$JS" | grep -q '"status":"ok"' || error "getNas not OK"
  URL=$(echo "$JS" | grep -o "https://cloudnas1\.ovh\.com/[0-9a-f]\{32\}\/")
  [ -n "$URL" ] || error "obtaining NAS URL"
  echo "$URL"
}

get_credentials() { # args: session
  local JS USERNAME SECRET
  JS=$(curl -s -A "$USERAGENT" -d "session=$1" \
         "$BASEURL/getCredentials")
  USERNAME=$(echo "$JS" | grep -o '"username":"[^"]*"' | cut -d\" -f 4)
  [ -n "$USERNAME" ] || error "obtaining username"
  SECRET=$(echo "$JS" | grep -o '"secret":"[^"]*"' | cut -d\" -f 4)
  [ -n "$SECRET" ] || error "obtaining secret"
  echo "$USERNAME / $SECRET"
}

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
  main "$@"
fi
