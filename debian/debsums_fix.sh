#!/bin/bash
# Fix sum for a package file that is reported wrong by debsums.
# Take the sum of the file on the filesystem as a reference and override the
# sum saved for the package. Most of the time it is because of docs or other
# non-sensitive files. If it is a binary or script, you better investigate.
# -- StalkR

PKGINFO="/var/lib/dpkg/info"

main() {
  if [ $# -lt 1 ]; then
    echo "Usage: $0 <file>"
    exit 1
  fi
  debsums_fix "$1"
}

debsums_fix() {
  local FILE SUMSFILE MATCHES
  FILE=$1

  SUMSFILE=$(grep -Hrl "^[a-f0-9]\{32\}  ${FILE:1}\$" "$PKGINFO" | sort)
  if [ -z "$SUMSFILE" ]; then
    error "File not found in any sums files."
  fi

  MATCHES=$(echo "$SUMSFILE" | wc -l)
  if [ $MATCHES -eq 1 ]; then
    update_sums "$FILE" "$SUMSFILE"

  elif [ $MATCHES -eq 2 ]; then
    fix_2sums "$SUMSFILE"

  else
    error "Multiple sums for this file," \
          "fix manually: grep \"${FILE:1}\" \"$SUMSFILE\""
  fi
}

update_sums() {
  local FILE SUMS NEWSUM OLDSUM
  FILE=$1
  SUMS=$2
  NEWSUM=$(md5sum "$FILE" | cut -d' ' -f1)
  OLDSUM=$(sed -n "s#\([0-9a-f]\{32\}\)  ${FILE:1}\$#\1#p" "$SUMS")

  if [ -z "$OLDSUM" ] || [ $(echo "$OLDSUM" | wc -l) -ne 1 ]; then
    error "No sum or multiples matches, should not happen here."

  elif [ "$OLDSUM" = "$NEWSUM" ]; then
    error "Sums are the same."

  else
    sed -i "s#$OLDSUM  \(.*\)#$NEWSUM  \1#" "$SUMS"
    echo "Updated $SUMS: $OLDSUM -> $NEWSUM."
  fi
}

fix_2sums() {
  local SUMSFILE FILE1 FILE2 ARCH FILE
  SUMSFILE=$1
  FILE1=$(basename "$(echo "$SUMSFILE" | head -1)")
  FILE2=$(basename "$(echo "$SUMSFILE" | tail -1)")
  ARCH=$(dpkg --print-architecture)
  if [ "${FILE1%.*}" = "${FILE2%.*}:$ARCH" ]; then
    echo "Two matches: $FILE1 and $FILE2, known arch bug, fixing file names."
    find "$PKGINFO" -name "${FILE1%.*}*" -print | while read FILE; do
      mv -v "$FILE" "${FILE%:$ARCH*}${FILE#*:$ARCH}"
    done
    echo "Done."

  else
    error "Two matches: $FILE1 and $FILE2, fix manually."
  fi
}

error() {
  echo "Error: $@" >&2
  exit 1
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
