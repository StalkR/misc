#!/bin/bash
# Duplicity backups wrapper (Linux or Windows with cygwin).

# A remote target like a mounted NFS on Linux or network drive on Windows.
# e.g. /mnt/nas/backups (Linux) or /cygdrive/e/backups (Windows)
declare -r TARGET="file:///mnt/nas/backups"

# Keep last 2 full backups and incremental, delete older backups.
declare -r ACTION="remove-all-but-n-full 2"

# Make a full backup after 30 days, encrypt with pgp@example.com public key.
declare -r OPTIONS="--full-if-older-than 30D --exclude-other-filesystems "\
"--exclude-if-present .nobackup --encrypt-key pgp@example.com"

# Backups: backup <name> <type> <path> [options]
backups() {
  # e.g. Linux
  backup boot dir /boot
  backup rootfs dir / --exclude /tmp
  # e.g. Windows
  # backup system dir /cygdrive/c
  # backup data   dir /cygdrive/d
}


### No modifications needed under this line.

# run runs the backups with logging: fd 1 (stdout) details, fd 3 summary.
run() {
  local begin elapsed

  if [[ "${TARGET:0:7}" = "file://" ]]; then
    if [[ ! -d "${TARGET:7}" ]]; then
      echo "Error: $@" >&2
      exit 1
    fi
  fi
  case "$(uname -o)" in
    Cygwin)
      # Cygwin soft limit is too low at 256, hard limit is 3200.
      ulimit -n 2048 ;;
  esac

  echo "$(hostname) backups on $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >&3
  begin=$(date '+%s')
  errors=0  # Global.
  backups
  elapsed=$[$(date '+%s') - $begin]
  echo "Done in $(duration $elapsed), $errors errors." >&3
  echo "Space used: $(used "$TARGET")" >&3
}

# backup performs a backup: clean, backup-command, collection status.
backup() {
  local name cmd begin elapsed
  name=$1
  cmd=$2
  shift 2
  begin=$(date '+%s')
  echo -n " * $name... " >&3
  echo "### Backup $TARGET/$name: $cmd $@"
  echo "* Clean"
  duplicity $ACTION --force "$TARGET/$name"
  echo
  echo "* Backup"
  "$cmd" "$name" "$@"
  if [[ $? -eq 0 ]]; then
    echo -n "OK" >&3
  else
    echo -n "fail" >&3
    errors=$[$errors + 1]
  fi
  elapsed=$[$(date '+%s') - $begin]
  echo " ($(used "$TARGET/$name"), $(duration $elapsed))" >&3
  echo
  echo "* Collection"
  duplicity collection-status "$TARGET/$name"
  echo
}

# dir backups a directory.
dir() {
  local name src
  name=$1
  src=$2
  shift 2
  duplicity $OPTIONS "$@" "$src" "$TARGET/$name"
}

# used displays space used by target. Only file:// supported.
used() {
  if [[ "${1:0:7}" = "file://" ]]; then
    du -sh "${1:7}" | cut -f1
    return
  fi
  echo "n/a"
}

# duration prints duration of a time in seconds in the most appropriate unit.
duration() {
  local t d h m s
  t=$1
  d=$[$t/60/60/24]
  h=$[($t-($d*60*60*24))/60/60]
  m=$[($t-($d*60*60*24)-($h*60*60))/60]
  s=$[$t-($d*60*60*24)-($h*60*60)-($m*60)]
  if [[ $d -gt 7 ]]; then
    echo "${d}d"
  elif [[ $d -gt 0 ]]; then
    echo "${d}d ${h}h"
  elif [[ $h -gt 0 ]]; then
    echo "${h}h ${m}m"
  elif [[ $m -gt 0 ]]; then
    echo "${m}m ${s}s"
  else
    echo "${s}s"
  fi
}

# main runs backups and outputs summary first then details.
main() {
  local tmp
  tmp=$(mktemp)
  { run > "$tmp"; } 3>&1
  echo
  cat "$tmp"
  rm -f "$tmp"
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
