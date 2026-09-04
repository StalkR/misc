#!/bin/bash
# Check latency with 1 ping for each bird peer via its neighbor address.
while read address; do
  name=${address#*%dn42-}
  echo -n "$name: "
  ping=$(ping -w 1 -c 1 "$address")
  r=$?
  if [[ $r -ne 0 ]]; then
    echo "timeout"
    continue
  fi
  latency=$(sed -n 's/.* time=\(.*\)/\1/p' <<< "$ping")
  echo "$latency"
done < <(sed -n 's/\s*Neighbor address: \(.*\)/\1/p' <(birdc show proto all))
