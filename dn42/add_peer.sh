#!/bin/bash
# Add a peer to WireGuard & bird, then bring up and configure.
# Listening port and link-local addresses are derived from the AS.

local_as="4242420000"
local_endpoint="example.com"

# ---

read -p "Peer AS number, without AS prefix: " peer_as

port="2${peer_as:6}"
ports_allocated=$(sed -n 's/^ListenPort\s*=\s*\(.*\)/\1/p' /etc/wireguard/*.conf | sort -n)
if ! grep -q "^${port}$" <<< "$ports_allocated"; then
  echo "port $port already in use"
  exit 1
fi

local_privkey=$(wg genkey)
local_pubkey=$(wg pubkey <<< "$local_privkey")
local_link="fe80::${local_as:6}"

echo "# Local"
echo "AS number: $local_as"
echo "WireGuard private key: $local_privkey"
echo "WireGuard public key: $local_pubkey"
echo "Endpoint: ${local_endpoint}:$port"
echo "Link-local address: $local_link"
echo

echo "# Peer"
echo "AS number: $peer_as"
read -p "WireGuard public key: " peer_pubkey
read -p "Endpoint: " peer_endpoint
peer_link="fe80:${peer_as:6}"
echo "Link-local address: ${peer_link}"
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
