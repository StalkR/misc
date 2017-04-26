#!/bin/bash
# Get & build grsec - last tested with 4.9.24
# For the script to work, be sure you already have successfully done the process
# manually once (added pgp keys, installed gcc plugins, etc).
# See also:
# - https://github.com/linux-scraping/linux-grsecurity
# - https://github.com/parazyd/grsecurity-scrape/

cd "$(dirname "${BASH_SOURCE[0]}")"

fail() {
  echo "Error: $@" >&2
  exit 1
}

[ -z "$BASH_VERSION" ] && fail "need bash"

GRSEC=$(curl "http://grsecurity.net/~spender/")
[ -n "$GRSEC" ] || fail "get grsecurity page"

PATCH=$(echo "$GRSEC" | grep -o 'grsecurity-[.0-9]*-[.0-9]*-[0-9]*\.patch' | sort -ru | head -n 1)
[ -n "$PATCH" ] || fail "parse patch file from grsec page"

wget -c "http://grsecurity.net/~spender/$PATCH" || fail "get $PATCH"
wget -c "http://grsecurity.net/~spender/$PATCH.sig" || fail "get $PATCH.sig"
gpg --verify "$PATCH.sig" || fail "wrong $PATCH signature"

KVER=$(echo "$PATCH" | sed 's/^grsecurity-[0-9.]\+-\([0-9.]\+\)-[0-9]\+\.patch/\1/')
[ -n "$KVER" ] || fail "parse kernel version"

MAJOR=${KVER%%.*} # a.b.c.d => a
REST=${KVER:${#MAJOR}+1} # => b.c.d
MINOR=${REST%%.*} # => b

TAR="linux-$KVER.tar"
XZ="$TAR.xz"
SIGN="$TAR.sign"
wget -c "http://www.kernel.org/pub/linux/kernel/v$MAJOR.x/$XZ" || fail "get $XZ"
wget -c "http://www.kernel.org/pub/linux/kernel/v$MAJOR.x/$SIGN" || fail "get $SIGN"

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
CONFIG=$(cd ..; echo config-* | tr ' ' '\n' \
  | sed 's/^config-//;s/-grsec$//' | sort -r | head -n 1)
CONFIG="../config-${CONFIG}-grsec"
[ -r "$CONFIG" ] || fail "no config file"
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
time CONCURRENCY_LEVEL=$(grep '^processor' /proc/cpuinfo | wc -l) \
  make-kpkg \
  --rootcmd fakeroot \
  --initrd \
  --revision "$(date '+%Y%m%d')" \
  kernel_image kernel_headers

# If there is already a deb for this version, already installed and running
# and you want to upgrade, use "--append-to-version -2".
