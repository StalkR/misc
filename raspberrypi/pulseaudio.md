# PulseAudio over network

## Overview

The sound server is a Linux computer (e.g. Raspberry Pi)
running PulseAudio,
connected to both your network (e.g. Wi-Fi or Ethernet)
and your sound system (e.g. with a 3.5 mm stereo jack).

The sound clients are Linux computers also running PulseAudio,
connected to the network (again, Wi-Fi or Ethernet).

## Setup

[PulseAudio docs](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Network/)
or
[ArchLinux wiki](https://wiki.archlinux.org/index.php/PulseAudio/Examples#PulseAudio\_over\_network)
explain multiple ways.

What worked for me is the TCP module with Zeroconf (Avahi).

* on the server, edit `/etc/pulse/default.pa` and add

        load-module module-native-protocol-tcp auth-anonymous=1
        load-module module-zeroconf-publish

  Note: `auth-anonymous=1` means any computer on the LAN can send audio.
  Alternatively, you can restrict IPs or copy the `~/.config/pulse/cookie` file.

* on the client, edit `/etc/pulse/default.pa` and add

        load-module module-zeroconf-discover


  Use `pavucontrol` if necessary to switch the default sink, then it remembers.

## Issues

Restarting the PulseAudio daemons on the server or clients generally helped
when sound did not work because the sink was not found, i.e. not discovered.

PulseAudio runs as the user (not a system-wide daemon),
`pulseaudio -k` kills the current instance
(and if it cannot find it, manual `ps` then `kill`)
and `pulseaudio -D` starts a new daemon.

If you cannot get Zeroconf (Avahi) to work (e.g. if not on the same LAN),
try to explicitly connect with
[`module-tunnel-sink`](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Modules/#index14h3).

I initially used Wi-Fi on the sound server, and likely because the connection
was not great, sound was sometimes cut. I switched to Ethernet and it works fine.
Interestingly, the client is on Wi-Fi and has no problem, likely because the
connection is better.
So I conclude Wi-Fi only works well if you have good connection, in particular no
latency spike.

## Windows

Compiled [WLStream](https://github.com/rsegecin/WLStream) and it works great.
From `cmd.exe` via a batch file, using
[cygwin](https://www.cygwin.com/) ssh:
`WLStream.exe | ssh server "pacat -p --format float32le"`.

Another solution could be [scream](https://github.com/duncanthrax/scream)
but I did not try.
