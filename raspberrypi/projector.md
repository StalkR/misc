# Projector setup

Constraints:

 - projector is attached to the ceiling, has power but no Ethernet.
 - sound system is next to the wall, has power and Ethernet.

Problem: how to carry video to the projector and audio to the sound
system without cables.

Solution, with what I had available:

 - a
   [Raspberry Pi 3 Model B](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/)
   placed next to the projector (small enough),
   connected on Wi-Fi (good chip),
   powerful enough for video decoding (VLC) and web browsing
   (YouTube, [Spotify](spotify.md), di.fm),
   sending sound with [PulseAudio over network](pulseaudio.md),
   with a USB wireless keyboard and mouse for remote control
 - a Raspberry Pi 1 Model B placed next to the sound system,
   connected on Ethernet (no Wi-Fi chip),
   not very powerful but enough for a sound server with PulseAudio

Both using [Raspbian](https://www.raspbian.org/) GNU/Linux 9.8 (stretch).

## Rejected alternatives

[Chromecast](https://store.google.com/product/chromecast) seemed nice,
it can carry video signal from a computer up to the projector, but it
wants to carry both video+audio while I need audio going somewhere else.
I had a workaround with a computer next to the sound system, using cast
by sharing desktop without audio, so it would send video to the Chromecast
but the audio would go out normally to the sound system.
But there are many problems with this setup:
it requires a computer next to the sound system,
desktop sharing requires heavy video encoding,
and introduces a noticeable ~500ms delay between video and sound,
and not all applications can handle it, for instance VLC can but not
if watching a video on YouTube in the browser.
