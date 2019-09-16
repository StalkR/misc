`lxc-debian` is from `lxc-templates` package on Debian 10 (buster),
unmodified so it can be diffed.

`lxc-debian-stalkr` is my patched version with:

* use `/etc/network/interfaces.d/{lo,eth0}` files instead of
  `interfaces`
* fix timezone, remove `/etc/localtime` pointing to `Etc/UTC` or it
  takes precedence
* do not install `openssh-server`
* install a few other packages by default:
  `curl deborphan etckeeper gnupg2 htop most procps psmisc vim`

See the diff: `diff -u lxc-debian lxc-debian-stalkr`
