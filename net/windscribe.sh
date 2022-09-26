#!/bin/bash
# Generate OpenVPN configs for Windscribe.
set -e

username='xxx'
password='xxx'
epoch=$(date '+%s')
# https://github.com/Windscribe/Desktop-App/blob/master/common/utils/hardcodedsettings.ini#L6
key='952b4412f002315aa50751032fcaab03'
# https://github.com/Windscribe/Desktop-App/blob/master/client/engine/engine/serverapi/serverapi.cpp#L99
client_auth_hash=$(echo -n "$key$epoch" | md5sum | cut -d' ' -f1)

useragent='Mozilla/5.0'

login=$(curl -sA "$useragent" -d "username=$username&password=$password&session_type_id=3&time=$epoch&client_auth_hash=$client_auth_hash" "https://api.windscribe.com/Session")
session_auth_hash=$(echo "$login" | python2 -c 'import json,sys; print json.load(sys.stdin)["data"]["session_auth_hash"]')

config=$(curl -sA "$useragent" "https://api.windscribe.com/ServerConfigs?session_auth_hash=$session_auth_hash&time=$epoch&client_auth_hash=$client_auth_hash")
echo "$config" | base64 -d > windscribe.cfg

creds=$(curl -sA "$useragent" "https://api.windscribe.com/ServerCredentials?session_auth_hash=$session_auth_hash&time=$epoch&client_auth_hash=$client_auth_hash")
echo "$creds" | python2 -c 'import base64,json,sys; d=json.load(sys.stdin)["data"]; print base64.b64decode(d["username"]); print base64.b64decode(d["password"])' > windscribe.auth
echo "[+] windscribe.auth"

servers=$(curl -sA "$useragent" "https://api.windscribe.com/ServerLocations?session_auth_hash=$session_auth_hash&time=$epoch&client_auth_hash=$client_auth_hash")
echo "$servers" > servers.json
echo "$servers" | python2 -c 'import json,sys; h=[]; [[h.append(n["hostname"]) for n in e["nodes"]] for e in json.load(sys.stdin)["data"] if "nodes" in e]; print "\n".join(";remote %s 443" % e for e in h)' > servers.list

sed -i 's/^auth-user-pass$/auth-user-pass windscribe.auth/' windscribe.cfg
sed -i 's/^dev tun$/dev tun0/' windscribe.cfg
cat windscribe.cfg servers.list > windscribe.conf
echo "[+] windscribe.conf"

rm -f windscribe.cfg servers.json servers.list

