# PulseAudio over network

## Overview

The sound server is a Linux computer (e.g. Raspberry Pi)
running PulseAudio,
connected to both your network (e.g. Wi-Fi or Ethernet)
and your sound system (e.g. with a 3.5 mm stereo jack).

The sound clients are just connected to the network:

* a Linux computer also running PulseAudio
* a Windows computer running
  [winpulse](https://github.com/StalkR/misc/blob/master/pulseaudio/winpulse/winpulse.go)

## Setup

[PulseAudio docs](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Network/)
or
[ArchLinux wiki](https://wiki.archlinux.org/index.php/PulseAudio/Examples#PulseAudio\_over\_network)
explain multiple ways.

What worked for me is the TCP module with Zeroconf (Avahi).

* on the server, edit `/etc/pulse/default.pa` and add

        load-module module-native-protocol-tcp auth-anonymous=1
        load-module module-zeroconf-publish

  Note: `auth-anonymous=1` means any computer on the network can send audio.
  Alternatively, you can restrict IPs or copy the `~/.config/pulse/cookie` file.

* on the Linux client, edit `/etc/pulse/default.pa` and add

        load-module module-zeroconf-discover


  Use `pavucontrol` if necessary to switch the default sink, then it remembers.

## Windows

I created my own solution in Go:
[`winpulse`](https://github.com/StalkR/misc/blob/master/pulseaudio/winpulse)
captures local Windows Audio and sends it to a PulseAudio server using the
native protocol like other Linux clients, with anonymous authentication.
It also supports sending over SSH by running `pacat` on the server,
which can be useful if you do not want to expose the PulseAudio server on
the network or if going through SSH hops.

It uses these small libraries:

* [`github.com/StalkR/misc/windows/audio`](https://godoc.org/github.com/StalkR/misc/windows/audio)
  to capture local audio on Windows
* [`github.com/StalkR/misc/pulseaudio`](https://godoc.org/github.com/StalkR/misc/pulseaudio)
  to send audio using PulseAudio native protocol

## Issues

Restarting the PulseAudio daemons on the server or clients generally helped
when sound did not work because the sink was not found, i.e. not discovered.

PulseAudio usually runs as the user instead of a system-wide daemon,
`pulseaudio -k` kills the current instance
(and if it cannot find it, manual `ps` then `kill`)
and `pulseaudio -D` starts a new daemon.

If you cannot get Zeroconf (Avahi) to work (e.g. if not on the same network),
try to explicitly connect with
[`module-tunnel-sink`](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Modules/#index14h3).

I initially used Wi-Fi on the sound server, and likely because the connection
was not great, sound was sometimes cut. I switched to Ethernet and it works fine.
Interestingly, the client is on Wi-Fi and has no problem, likely because the
connection is better.
So I conclude Wi-Fi only works well if you have good connection, in particular no
latency spike.

For Windows I tried [WLStream](https://github.com/rsegecin/WLStream), compiled it
then from `cmd.exe` stream it via ssh
(e.g. `WLStream.exe | ssh server "pacat -p --format float32le"`).
It works but has stutters every minute, probably because of the
pipe to ssh, so I made my own
([`winpulse`](https://github.com/StalkR/misc/blob/master/pulseaudio/winpulse/winpulse.go)).

Another Windows solution could have been [scream](https://github.com/duncanthrax/scream)
but I did not try as it requires its own receiver on the server.
