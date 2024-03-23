#!/bin/bash
# Generate OpenVPN configs for Windscribe.
set -e
username=''
password=''

if [[ -z "$username" ]] || [[ -z "$password" ]]; then
  echo "missing username/password"
  exit 1
fi

epoch=$(date '+%s')
# https://github.com/Windscribe/Desktop-App/blob/master/common/utils/hardcodedsettings.ini#L6
key='952b4412f002315aa50751032fcaab03'
# https://github.com/Windscribe/Desktop-App/blob/master/client/engine/engine/serverapi/serverapi.cpp#L99
client_auth_hash=$(echo -n "$key$epoch" | md5sum | cut -d' ' -f1)

useragent='Mozilla/5.0'

login=$(curl -sA "$useragent" -d "username=$username&password=$password&session_type_id=3&time=$epoch&client_auth_hash=$client_auth_hash" "https://api.windscribe.com/Session")
used=$(echo "$login" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["traffic_used"])')
max=$(echo "$login" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["traffic_max"])')
percent=$((100*$used/$max))
remain=$((($max-$used)/1024/1024))MB
used=$(($used/1024/1024))MB
max=$(($max/1024/1024))MB
lastreset=$(echo "$login" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["last_reset"])')
echo "[*] traffic used: $used/$max ($percent%) $remain remaining, last reset $lastreset"
if [[ $percent -gt 100 ]]; then
  echo "[-] out of quota"
  exit 1
fi
if [[ -n "$QUOTA" ]]; then
  exit 0
fi
session_auth_hash=$(echo "$login" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["session_auth_hash"])')

config=$(curl -sA "$useragent" "https://api.windscribe.com/ServerConfigs?session_auth_hash=$session_auth_hash&time=$epoch&client_auth_hash=$client_auth_hash")
echo "$config" | base64 -d > windscribe.cfg

creds=$(curl -sA "$useragent" "https://api.windscribe.com/ServerCredentials?session_auth_hash=$session_auth_hash&time=$epoch&client_auth_hash=$client_auth_hash")
echo "$creds" | python3 -c 'import base64,json,sys; d=json.load(sys.stdin)["data"]; print(base64.b64decode(d["username"]).decode()); print(base64.b64decode(d["password"]).decode())' > windscribe.auth || { echo "$creds"; exit 1; }
echo "[+] windscribe.auth"

servers=$(curl -sA "$useragent" "https://api.windscribe.com/ServerLocations?session_auth_hash=$session_auth_hash&time=$epoch&client_auth_hash=$client_auth_hash")
echo "$servers" > servers.json
echo "$servers" | python3 -c 'import json,sys; h=[]; [[h.append(n["hostname"]) for n in e["nodes"]] for e in json.load(sys.stdin)["data"] if "nodes" in e]; print("\n".join(";remote %s 443" % e for e in sorted(h)))' > servers.list
sed -i '1 s/^;//' servers.list

sed -i 's/^auth-user-pass$/auth-user-pass windscribe.auth/' windscribe.cfg
sed -i 's/^dev tun$/dev tun0/' windscribe.cfg
cat windscribe.cfg servers.list > windscribe.conf
echo "[+] windscribe.conf"

rm -f windscribe.cfg servers.json servers.list
