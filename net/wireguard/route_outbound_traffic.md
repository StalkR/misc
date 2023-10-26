# Routing outbound traffic via another server

Imagine your internet provider blocks outbound tcp/25 (SMTP), but you still
want to be able to: you can use wireguard to route this traffic elsewhere.

## Client

Install wireguard: `apt install wireguard`

Configure it: `/etc/wireguard/wg0.conf`

```
[Interface]
PrivateKey = [wg genkey]
Address = 10.0.0.2/24

# wireguard uses table 51820 by default but it may be more if it already exists
# in our case this table does not exist so we know wireguard is using 51820
PostUp = ip -4 rule delete table 51820; ip -4 rule delete table main suppress_prefixlength 0; ip -4 rule add priority 1000 dport 25 table 10; ip -4 route add default via 10.0.0.1 table 10
PostDown = ip -4 rule delete priority 1000

[Peer]
Endpoint = server:51820
PublicKey = [add]
# we use this wireguard to route outbound tcp/25
# we need 0.0.0.0/0 in allowed ips or packets will be dropped
# but this causes wireguard to set itself as default route
# which we do not want so we must revert
# and then we add our rule for outbound tcp/25
AllowedIPs = 10.0.0.0/24,0.0.0.0/0
```

Configure auto-start: `systemctl enable wg-quick@wg0`
Start it: `systemctl start wg-quick@wg0`

## Server

Assuming you already have a wireguard server acting as gateway.

Add the new client: `/etc/wireguard/wg0.conf`

Restart: `systemctl restart wg-quick@wg0`

Update firewall to allow only the traffic you want: `/etc/ferm/ferm.conf`

```
domain (ip ip6) {
  table filter {
    chain FORWARD {
      saddr (10.0.0.2) {
        # we want to be able to connect to it (e.g. ssh) so allow responses
        mod state state (ESTABLISHED RELATED) ACCEPT;
        # allow outbound tcp/25 but nothing else
        proto tcp dport 25 ACCEPT;
        DROP;
      }
    }
  }
}
```
