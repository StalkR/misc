# Remote unlock LUKS disk encryption

This guide describes how to set up and boot a remote server with disk
encryption, using a script in initramfs that sets up networking then listens
for the LUKS key over TLS using socat.

It can use DHCP or static IP configuration and listens on a fixed port, but you
may adapt it to other configurations.

## Pre-requisites

Install your remote server however you want (live cd or rescue mode), create
your LUKS, install your system, etc. we will focus on configuring the boot.


## Install socat

Using Debian for this guide:

```
apt install -y socat
```

## Create server certificate

Change:

 - `example.net` with your hostname

```
mkdir -p /etc/cryptroot && cd /etc/cryptroot
openssl req -subj '/CN=example.net' -new -newkey rsa:4096 -sha256 -days 36500 -nodes -x509 -keyout server.key -out server.crt
openssl dhparam -out dhparams.pem 2048
cat server.{key,crt} dhparams.pem > server.pem
```

Copy `server.crt` to the client you will use to remotely boot the server.

## Add initramfs hook

Install everything we need in the initramfs next time it's updated:

```
cat << EOF > /etc/initramfs-tools/hooks/cryptroot
#!/bin/sh -e
case "\$1" in
    prereqs) echo ""; exit 0;;
esac

# provides copy_exec()
. /usr/share/initramfs-tools/hook-functions

copy_exec /usr/bin/socat /bin/
mkdir -p \$DESTDIR/etc/cryptroot
cp /etc/cryptroot/server.pem \$DESTDIR/etc/cryptroot
EOF
chmod a+x /etc/initramfs-tools/hooks/cryptroot
```

## Configuring network

We'll use Linux [ipconfig][ipconfig], configuring network directly on kernel
cmdline:

 - DHCP: `ip=:::::eth0:dhcp`
 - static IP: `ip=192.168.0.1:::::eth0:none`

[ipconfig]: https://git.kernel.org/pub/scm/libs/klibc/klibc.git/tree/usr/kinit/ipconfig/README.ipconfig

Then we use standard initramfs functions to initialize networking from that:

```
. /scripts/functions
configure_networking
```

## Script to receive the key

Set up networking, listen for the key, write it to stdout, deconfigure
networking and resume boot.

Change `1337` with the port you want to listen on.

```
cat << EOF > /etc/cryptroot/key.sh
#!/bin/sh
{
  echo "Configure network..."
  . /scripts/functions
  configure_networking
  echo "Waiting for remote key..."
} >&2
socat openssl-listen:1337,reuseaddr,cert=/etc/cryptroot/server.pem,verify=0 STDOUT
EOF
chmod a+x /etc/cryptroot/key.sh
```

## Configure crypttab

Crypttab is what the system uses to unlock encrypted partitions.
Instruct it to use our script to get the key.

Change:

- `/dev/sda2` with the encrypted device
- `pvcrypt` with the device mapper name for the unlocked device

```
cat << EOF > /etc/crypttab
# <target name> <source device>         <key file>      <options>
pvcrypt         /dev/sda2               none            luks,keyscript=/etc/cryptroot/key.sh
EOF
```

## Update initramfs

Regenerate the initramfs to take into account our modifications:

```
update-initramfs -tuck $(uname -r)
```

## Reboot and unlock remotely

Now reboot, and pray that it boots correctly.
It should set up networking, which you can notice because it will respond to
pings, then it should listen for the key, which you can send with socat.

Change:

- `example.net` with your hostname
- `1337` with the listening port you chose

```
socat - openssl-connect:example.net:1337,verify=1,cafile=server.crt < <(read x; echo -n "$x")
```

Copy the key and press enter.

Your server should now unlock disk and continue booting.
