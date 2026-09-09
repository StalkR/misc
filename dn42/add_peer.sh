#!/bin/bash
# Add a peer to WireGuard & bird, then bring up and configure.
# Ports are allocated incrementally and if available.

# port range, min/max both included
min_port=51821
max_port=52000

# typically fe80:: followed by the last 4 digits of your AS
local_link="fe80::1248"

# ---

ports_allocated=$(sed -n 's/^ListenPort\s*=\s*\(.*\)/\1/p' /etc/wireguard/*.conf | sort -n)
port=$min_port
while :; do
  if ! grep -q "^${port}$" <<< "$ports_allocated"; then
    break
  fi
  port=$(($port + 1))
  if [[ $port -gt $max_port ]]; then
    echo "all local ports allocated"
    exit 1
  fi
done

local_privkey=$(wg genkey)
local_pubkey=$(wg pubkey <<< "$local_privkey")

echo "# Local"
echo "WireGuard public key: $local_pubkey"
echo "Endpoint: dn42.stalkr.net:$port"
echo "Link local: $local_link"
echo

echo "# Peer"
read -p "AS number, without AS prefix: " peer_as
read -p "Link local: " peer_link
read -p "WireGuard pubkey: " peer_pubkey
read -p "WireGuard endpoint: " peer_endpoint
echo

config_wg="/etc/wireguard/as${peer_as}.conf"
config_bird="/etc/bird/peers/as${peer_as}.conf"

echo "Writing config: ${config_wg}"
cat > "${config_wg}" << EOF
[Interface]
PrivateKey = ${local_privkey}
Address = ${local_link}/64
ListenPort = ${port}
PostUp = /sbin/sysctl -w net.ipv4.conf.all.rp_filter=0 net.ipv4.conf.%i.rp_filter=0
Table = off

[Peer]
PublicKey = ${peer_pubkey}
Endpoint = ${peer_endpoint}
AllowedIPs = 172.16.0.0/12, 10.0.0.0/8, fd00::/8, fe80::/10
EOF
chmod o-rwx "${config_wg}"

echo "Writing config: ${config_bird}"
cat > "${config_bird}" << EOF
protocol bgp as${peer_as} from dnpeers {
    enable extended messages on;
    neighbor ${peer_link} as ${peer_as};
    interface "as${peer_as}";

    ipv4 {
        extended next hop on;
    };
};
EOF

echo "Bring up WireGuard"
wg-quick up "as${peer_as}" || {
  rm -f "${config_wg}" "${config_bird}"
  exit 1
}
echo

echo "Configure bird"
birdc configure || {
  wg-quick down "as${peer_as}"
  echo "-----------"
  cat "${config_bird}"
  echo "-----------"
  rm -f "${config_wg}" "${config_bird}"
  exit 1
}
echo

echo "Done"
