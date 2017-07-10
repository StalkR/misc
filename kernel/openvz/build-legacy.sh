#!/bin/bash
# Get and build latest OpenVZ legacy rhel6 kernel.
# Pre-requisites:
# - imported OpenVZ gpg public key (https://wiki.openvz.org/Package_signatures)
# - a config-2.6.32-* file (start with one from OpenVZ)
# - linux-2.6.32.tar.bz2 archive (https://www.kernel.org/pub/linux/kernel/v2.6/)

cd "$(dirname "${BASH_SOURCE[0]}")"

PREVIOUS=$(ls -t config-2.6.32-* | head -1 | cut -d- -f3)

CURRENT=$1
if [[ -z "$CURRENT" ]]; then
  page=$(curl -s 'https://openvz.org/Download/kernel')
  #CURRENT=$(echo "$page" | sed -n 's#.*rhel6-testing/\([^"]\+\).*#\1#p')
  CURRENT=$(echo "$page" | sed -n 's#.*rhel6/\([^"]\+\).*#\1#p' | head -1)
fi

echo "Previous: $PREVIOUS - Current: $CURRENT"
if [[ $PREVIOUS = $CURRENT ]]; then
  echo "Nothing to do"
  exit 1
fi

wget -qc "http://download.openvz.org/kernel/branches/rhel6-2.6.32-testing/${CURRENT}/patches/patch-${CURRENT}-combined.gz" || \
  wget -qc "http://download.openvz.org/kernel/branches/rhel6-2.6.32/${CURRENT}/patches/patch-${CURRENT}-combined.gz" || \
  exit 1
wget -qc "http://download.openvz.org/kernel/branches/rhel6-2.6.32-testing/${CURRENT}/patches/patch-${CURRENT}-combined.gz.asc" || \
  wget -qc "http://download.openvz.org/kernel/branches/rhel6-2.6.32/${CURRENT}/patches/patch-${CURRENT}-combined.gz.asc" || \
  exit 1

check_exists() {
  if [[ ! -f "$1" ]]; then
    echo "Error: $1 missing" >&2
    exit 1
  fi
}

check_exists linux-2.6.32.tar.bz2
check_exists config-2.6.32-${PREVIOUS}
check_exists patch-${CURRENT}-combined.gz
check_exists patch-${CURRENT}-combined.gz.asc

if ! gpg --verify patch-${CURRENT}-combined.gz.asc 2>/dev/null; then
  echo "Error: patch-${CURRENT}-combined.gz wrong signature" >&2
  exit 1
fi

[[ -e linux-2.6.32 ]] && rm -rf linux-2.6.32
tar jxf linux-2.6.32.tar.bz2
cd linux-2.6.32
zcat ../patch-${CURRENT}-combined.gz | patch -p1
for p in ../*.patch; do
  echo "Applying $p"
  patch -p1 < "$p"
done

cp ../config-2.6.32-${PREVIOUS} .config
make-kpkg clean
echo | make oldconfig
cp .config ../config-2.6.32-${CURRENT}
revision=$(date '+%Y%m%d')
time make-kpkg --initrd --revision $revision --append-to-version -${CURRENT} kernel_image
