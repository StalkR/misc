#!/bin/bash
# Fix sum for a package file that is reported wrong by debsums.
# Take the sum of the file on the filesystem as a reference and override the
# sum saved for the package. Most of the time it is because of docs or other
# non-sensitive files. If it is a binary or script, you better investigate.
# -- StalkR

PKGINFO="/var/lib/dpkg/info"

main() {
  local FILE NEWSUM LIST SUMS FILENOROOT OLDSUM
  if [ $# -lt 1 ]; then
    echo "Usage: $0 <file>"
    exit 1
  fi
  FILE=$1

  NEWSUM=$(md5sum "$FILE" | cut -d' ' -f1)
  LIST=$(grep -Hrl "^$FILE\$" "$PKGINFO")
  [ -z "$LIST" ] && error "File not found in any package."
  [ $(echo "$LIST" | wc -l) -ne 1 ] && \
    error "Multiple matches for this file." \
          "See: grep -Hr \"$FILE\" \"$PKGINFO\""
  SUMS=${LIST%.*}.md5sums
  [ ! -f "$SUMS" ] && error "No $SUMS file."
  # files do not have the / at the beginning
  FILENOROOT=${FILE#/*}
  OLDSUM=$(sed -n "s#\([0-9a-f]\{32\}\)  $FILENOROOT\$#\1#p" "$SUMS")
  [ -z "$OLDSUM" ] && error "Cannot find file in sums file $SUMS."
  [ $(echo "$OLDSUM" | wc -l) -ne 1 ] && \
    error "Multiple sums for this file?" \
          "See: grep \"$FILENOROOT\" \"$SUMS\""
  [ "$OLDSUM" == "$NEWSUM" ] && error "Sums are the same."
  sed -i "s#$OLDSUM  \(.*\)#$NEWSUM  \1#" "$SUMS"
  echo "Sums updated."
}

error() {
  echo "Error: $@" >&2
  exit 1
}

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
  main "$@"
fi

