#!/bin/bash
# Create DI playlists for mpd.

declare -r LISTENKEY='xxxx'
declare -a RADIOS=(
  classicalradio.com
  di.fm
  jazzradio.com
  radiotunes.com
  rockradio.com
  zenradio.com
)

pushd '/var/lib/mpd/playlists'

for radio in "${RADIOS[@]}"; do
  i=0
  keys=$(curl -s "http://listen.${radio}/streamlist" | jq -r '.[] | .key')
  while read key; do
    echo "http://prem2.${radio}:80/${key}?${LISTENKEY}"
    i=$(($i+1))
  done <<< "$keys" > "${radio}.m3u"
  echo "Created: ${radio}.m3u ($i channels)"
done
