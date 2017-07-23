# systemd hacks

I tried to accept systemd on my Debian systems, but it's
just so broken. Below are some of the most annoying issues
I had and how I worked around them. Not exhaustive.

Eventually I removed systemd, my systems are back to being
stable and I am much happier.

 * http://without-systemd.org
 * https://www.devuan.org/


## Cannot shutdown

```
# poweroff
Failed to talk to init daemon.
```

Never found a solution other than force: `sync && reboot -f`


## Zombies piling up

After a while I noticed a bunch of zombies on my servers, wtf?
Init has one job, reap zombies with waitpid(). Simple right? Well, not for
systemd it seems.
The clean-zombies script uses gdb to attach to init and calls waitpid to
reap zombies.


## Boot hanging on systemd-tmpfiles

Disable this shit with:

```
systemctl mask systemd-tmpfiles-setup.service
```

And reboot.


## Nullmailer hang on systemd-tmpfiles

One more issue because of systemd-tmpfiles, this time in a postinst script
for nullmailer.
The maintainer thought it would be a good idea to use systemd to create the
fifo using yet another systemd thing instead of doing directly.
Why does systemd had to invent a configuration language to create these files
and why does systemd-tmpfiles even exist is beyond me, but worse is they
could not make it work.

```
sed -i 's@\(\s*systemd-tmpfiles.*\)@#\1\n\t\tf=/var/spool/nullmailer/trigger\n\t\trm -f "$f" \&\& mkfifo "$f" \&\& chmod 622 "$f" \&\& chown mail:root "$f"@' /var/lib/dpkg/info/nullmailer.postinst
```
