#!/bin/bash
# Get & build grsec - works for linux >= 3.0.5, last tested with 3.17.7
# Notes:
#  * since 3.x, files are in /v3.0/ (even if x > 0)
#  * since 3.0.5, only the .tar is signed (and no longer compressed archives)
#  * save your kernel configs in the same directory, last edited is used
# For the script to work, be sure you already have successfully done the process
# manually once (added pgp keys, installed gcc plugins, etc).

fail() {
  echo "Error: $@" >&2
  exit 1
}

[ -z "$BASH_VERSION" ] && fail "need bash"

GRSEC=$(curl http://grsecurity.net/test.php)
[ -n "$GRSEC" ] || fail "get grsecurity page"

PATCH=$(echo "$GRSEC" | grep -o 'test/grsecurity-[.0-9]*-[.0-9]*-[0-9]*\.patch' | sort -ru | head -n 1 | cut -c6-)
[ -n "$PATCH" ] || fail "parse patch file from grsec page"

wget -c "http://grsecurity.net/test/$PATCH" || fail "get $PATCH"
wget -c "http://grsecurity.net/test/$PATCH.sig" || fail "get $PATCH.sig"
gpg --verify "$PATCH.sig" || fail "wrong $PATCH signature"

KVER=$(echo "$PATCH" | sed 's/^grsecurity-[0-9.]\+-\([0-9.]\+\)-[0-9]\+\.patch/\1/')
[ -n "$KVER" ] || fail "parse kernel version"

MAJOR=${KVER%%.*} # a.b.c.d => a
REST=${KVER:${#MAJOR}+1} # => b.c.d
MINOR=${REST%%.*} # => b

TAR="linux-$KVER.tar"
XZ="$TAR.xz"
SIGN="$TAR.sign"
wget -c "http://www.kernel.org/pub/linux/kernel/v$MAJOR.0/$XZ" || fail "get $XZ"
wget -c "http://www.kernel.org/pub/linux/kernel/v$MAJOR.0/$SIGN" || fail "get $SIGN"

echo
echo "Decompress..."
xz --decompress --keep "$XZ" || fail "decompress $XZ"

gpg --verify "$SIGN" || fail "wrong $SIGN signature"

echo
echo "Remove old build..."
rm -rf "linux-$KVER"

echo
echo "Extract..."
tar xf "$TAR" || fail "extract $TAR"
rm -f "$TAR" || fail "remove $TAR"
cd "linux-$KVER" || fail "cd linux-$KVER"
patch -p1 < "../$PATCH" || fail "apply $PATCH"

echo
echo "Configure..."
CONFIG=$(echo ../config-* | tr ' ' '\n' | sort -r | head -n 1)
[ -n "$CONFIG" ] || fail "no config file"
cp "$CONFIG" .config
# Using old config
if [ "$CONFIG" != "../config-$KVER-grsec" ]; then
  # answer default to all questions
  echo | make oldconfig
  cp .config "../config-$KVER-grsec"
fi

echo
echo "Clean..."
make-kpkg clean
echo
echo "Build..."
# Use KCONFIG_OVERWRITECONFIG to avoid scripts/kconfig/conf creating .config.old
# but still for some reason it ends up in the .deb as /boot/config-xxx.old :(
time KCONFIG_OVERWRITECONFIG=1 \
  CONCURRENCY_LEVEL=$(grep '^processor' /proc/cpuinfo | wc -l) \
  make-kpkg \
  --rootcmd fakeroot \
  --initrd \
  --revision "$(date '+%Y%m%d')" \
  kernel_image kernel_headers

# If there is already a deb for this version, already installed and running
# and you want to upgrade, use "--append-to-version -2".
