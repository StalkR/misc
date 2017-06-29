#!/bin/bash
# Increment serial in a zone file in BIND format.
# Looks for a "XXXXXXXXXX ; serial" line and increments it.

main() {
  if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <zone file> [...]"
    exit 1
  fi
  while [[ -n "$1" ]]; do
    increment "$1"
    shift
  done
}

increment() {
  serial=$(sed -n '/; serial$/s/\s*\([0-9]\+\).*/\1/p' "$1")
  if [[ -z "$serial" ]]; then
    echo "Error: could not find serial in zone file $1" >&2
    exit 2
  fi
  next=$(($serial+1))
  sed -i "/; serial$/s/$serial/$next/" "$1"
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
