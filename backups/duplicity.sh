#!/bin/bash
# Duplicity backups wrapper (Linux or Windows with cygwin).

# A remote target like a mounted NFS on Linux or network drive on Windows.
# e.g. /media/nas/backups (Linux) or /cygdrive/e/backups (Windows)
declare -r TARGET="file:///media/nas/backups"
# Keep last 2 full backups and incremental, delete older backups.
declare -r ACTION="remove-all-but-n-full 2"
# Make a full backup after 30 days, encrypt with pgp@example.com public key.
declare -r OPTIONS="--full-if-older-than 30D --exclude-other-filesystems "\
"--encrypt-key pgp@example.com"

run() {
  local dest begin elapsed

  if [[ "${TARGET:0:7}" = "file://" ]]; then
    dest=${TARGET:7}
    if [[ ! -d "$dest" ]]; then
      err "$dest does not exist"
    fi
  fi
  ulimit -n 2048  # Cygwin soft limit is too low at 256, hard limit is 3200.

  echo "$(hostname) backups on $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >&3
  begin=$(date '+%s')
  errors=0  # Global.

  # Configure backups here.
  # e.g. Linux
  backup rootfs dir /
  backup boot dir /boot
  # e.g. Windows
  # backup system dir /cygdrive/c
  # backup data   dir /cygdrive/d

  elapsed=$[$(date '+%s') - $begin]
  echo "Done in $(duration $elapsed), $errors errors." >&3
  echo "Space used: $(used "$TARGET")" >&3
}

backup() {
  local name cmd begin elapsed
  name=$1
  cmd=$2
  shift 2
  begin=$(date '+%s')
  echo -n " * $name... " >&3
  echo "### Backup $@"
  echo "* Clean"
  duplicity $ACTION --force "$TARGET/$name"
  echo
  echo "* Backup"
  $cmd "$name" "$@"
  if [[ $? -eq 0 ]]; then
    echo -n "OK" >&3
  else
    echo -n "fail" >&3
    errors=$[$errors + 1]
  fi
  elapsed=$[$(date '+%s') - $begin]
  echo " ($(used "$TARGET/$name"), $(duration $elapsed))" >&3
  echo "* Collection"
  duplicity collection-status "$TARGET/$name"
  echo
}

# Backup a directory, excludes in $more with --exclude /abs/path
dir() {
  local name src more
  name=$1
  src=$2
  more=$3
  duplicity $OPTIONS $more "$src" "$TARGET/$name"
}

used() {
  if [[ "${1:0:7}" = "file://" ]]; then
    du -sh "${1:7}" | cut -f1
    return
  fi
  echo "n/a"
}

# Human duration of a time in seconds in most appropriate unit.
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

lock() {
  if ! [[ -x "$(command -v flock)" ]]; then
    err "flock not available"
  fi
  if [[ -z "$LOCKED" ]]; then
    LOCKED=1 flock -nox "/var/lock/backup_$1" "$0"
    exit $?
  fi
}

err() {
  echo "Error: $@" >&2
  exit 1
}

main() {
  local name=$(basename "${BASH_SOURCE[0]}")
  lock "$name"
  { run >"/var/log/backup_$name.log"; } 3>&1
  echo
  cat "/var/log/backup_$name.log"
}

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
