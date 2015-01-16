# DNS Proxy #
Binary proxy is a DNS reverse proxy to route queries to different DNS servers.
It listens on both TCP/UDP IPv4/IPv6 on specified port.
Since the upstream servers will not see the real client IPs but the proxy,
you can specify a list of IPs allowed to transfer (AXFR/IXFR).

Example usage:

    $ go run proxy.go -address ':53' \
        -default '8.8.8.8:53' \
        -route '.example.com.=8.8.4.4:53' \
        -allow-transfer '1.2.3.4,5.6.7.8'

A query for `example.net` or `example.com` will go to `8.8.8.8:53`, the default.
However, a query for `subdomain.example.com` will go to `8.8.4.4:53`.

# Install #

    $ cd /tmp
    $ wget https://github.com/StalkR/misc/raw/master/dns/proxy/proxy.go
    $ go build proxy.go
    $ mv proxy /usr/local/bin/proxy
    $ rm -f proxy.go
    $ wget https://github.com/StalkR/misc/raw/master/dns/proxy/etc/init.d/proxy -O /etc/init.d/proxy
    $ chmod +x /etc/init.d/proxy
    $ insserv proxy

# Configure #

    vi /etc/default/proxy

Example:

    # Allow transfer from: puck.nether.net
    DAEMON_ARGS="-default 127.0.0.1:1053 -route '.example.com.=127.0.0.1:2053' -allow-transfer '204.42.254.5'"

# Start/Stop #

    invoke-rc.d proxy start
    invoke-rc.d proxy stop
    invoke-rc.d proxy restart
