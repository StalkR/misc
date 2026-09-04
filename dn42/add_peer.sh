#!/bin/bash
# Add a peer to WireGuard & bird, then bring up and configure.

local_privkey=$(wg genkey)
local_pubkey=$(wg pubkey <<< "$local_privkey")
lastport=$(sed -n 's/^ListenPort\s*=\s*\(.*\)/\1/p' /etc/wireguard/*.conf | sort -n | tail -1)
port=$(($lastport + 1))
local_link="fe80::1248"

echo "# Local"
echo "WireGuard public key: $local_pubkey"
echo "Endpoint: dn42.stalkr.net:$port"
echo "Link local: $local_link"
echo

echo "# Peer"
read -p "Name for this peer: " peer_name
read -p "AS number, without AS prefix: " peer_as
read -p "Link local: " peer_link
read -p "WireGuard pubkey: " peer_pubkey
read -p "WireGuard endpoint: " peer_endpoint
echo

config_wg="/etc/wireguard/dn42-${peer_name}.conf"
config_bird="/etc/bird/peers/${peer_name}.conf"

echo "Writing config: ${config_wg}"
cat > "${config_wg}" << EOF
# https://explorer.burble.com/#/aut-num/AS${peer_as}
# ping ${peer_link}%dn42-${peer_name}
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

echo "Writing config: ${config_bird}"
cat > "${config_bird}" << EOF
protocol bgp ${peer_name} from dnpeers {
    enable extended messages on;
    neighbor ${peer_link} as ${peer_as};
    interface "dn42-${peer_name}";

    ipv4 {
        extended next hop on;
    };
};
EOF

echo "Bring up WireGuard dn42-${peer_name}"
wg-quick up "dn42-${peer_name}" || {
  rm -f "${config_wg}" "${config_bird}"
  exit 1
}
echo

echo "Configure bird"
birdc configure || {
  wg-quick down "dn42-${peer_name}"
  echo "-----------"
  cat "${config_bird}"
  echo "-----------"
  rm -f "${config_wg}" "${config_bird}"
  exit 1
}

echo "Done, check: ping ${peer_link}%dn42-${peer_name}"
