# Spotify on Raspberry Pi

Using, as of 2019-04-16:

* [Raspberry Pi 3 Model B](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/)
* [Raspbian](https://www.raspbian.org/) GNU/Linux 9.8 (stretch)
* `chromium-browser` package version `72.0.3626.121-0+rp`

Problem: play anything on [Spotify](https://open.spotify.com/), nothing happens.

Cause: [apparently](https://gist.github.com/ruario/3c873d43eb20553d5014bd4d29fe37f1)
because of [DRM](https://en.wikipedia.org/wiki/Digital_rights_management),
specifically that Chromium does not include `libwidevinecdm.so` for `armhf`.

Solution: take `libwidevinecdm.so` from ChromeOS using
[ruario/widevine-flash\_armhf.sh](https://gist.github.com/ruario/19a28d98d29d34ec9b184c42e5f8bf29)
and put it in `/usr/lib/chromium-browser`.

Notes:

* the script also fetches `libpepflashplayer.so` but it is not needed
* on 2019-04-16 I had md5 `4946f3c49c7ce5cd129e66c61aab28a4` for `libwidevinecdm.so`

## Failed attempts

Firefox with package `firefox-esr` also misses the Widevine DRM module.
There is even a [bug report](https://bugzilla.mozilla.org/show_bug.cgi?id=1392037) about it.

Debian offers a [`chromium-widevine`](https://packages.debian.org/search?searchon=names&keywords=chromium-widevine)
package including for `armhf` but the [file list](https://packages.debian.org/stretch/armhf/chromium-widevine/filelist)
for all architectures shows it is empty.

Raspbian & Debian Chromium packages are actually different:
on Debian it is `chromium` while on Raspbian it is `chromium-browser`.
I tried adding Debian repositories and installing `chromium` but it fails to even start,
so I think messing up with the repos might not be recommended and could break your Raspbian - be careful.
