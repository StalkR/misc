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
