#!/bin/bash
# Sync files between two locations.
# Can be push or pull, optional delete, question or encryption.

# rsync remote shell to use, useful to set ssh options
declare -r RSH='ssh -i /mnt/nas/ssh.key'

# Sync: log <name> <action>
# Actions:
# - transfer|transfer_ask [options] <orig> [<orig> ...] <dest>
# - transfer_enc <key> <orig> <dest>
sync() {
  # Ensure directories are there (e.g. mounted)
  check_exists '/mnt/nas/backups'

  # Pull remote backups locally, delete when remote deletes stuff (full sync).
  log 'Pull backups' transfer --delete 'example.com:/mnt/backups/' '/mnt/nas/backups/'

  # Pull remote docs locally, do not delete anything if it disappears on remote.
  log 'Pull docs' transfer 'example.com:/mnt/docs/' '/mnt/nas/docs/'
  # Push local docs remotely, list files to upload and ask before continuing (if any).
  log "Push docs" transfer_ask '/mnt/nas/docs/' 'example.com:/mnt/docs/'

  # Push local photos remotely, encrypted with key using encfs.
  # Local files are untouched, encfs is used to push encrypted files to
  # destination, so that destination does not see files in clear.
  # It's a full sync, files are deleted remotely if local files are deleted.
  log 'Push photos' transfer_enc 'secret' '/mnt/nas/photos/' 'example.com:/mnt/photos/'

  # Trailing slash means contents of the directory, what we want (cf. rsync).
}


### No modifications needed under this line.

# Interactive shows details then summary, otherwise summary then details.
main() {
  local result tmp
  if [[ -z "$FLOCK" ]]; then
    FLOCK=1 flock -E 42 -nx "$0" "$0" "$@"
    result=$?
    [[ $result -eq 42 ]] && echo "Another sync already running" >&2
    exit $result
  fi
  tmp=$(mktemp)
  if interactive; then
    run 3>"$tmp"
  else
    { run >"$tmp" 2>&1; } 3>&1
  fi
  echo
  cat "$tmp"
  rm -f "$tmp"
}

interactive() {
  [[ -n "$TERM" ]] && [[ "$TERM" != "dumb" ]]
}

# run runs the sync with logging: fd 1 (stdout) details, fd 3 summary.
run() {
  local host begin elapsed
  host=$(hostname | tr -d '\r')
  echo "$host sync on $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >&3
  begin=$(date '+%s')
  errors=0  # global
  sync
  elapsed=$(duration $[$(date '+%s') - $begin])
  echo "Done in $elapsed, $errors errors." >&3
}

log() {
  local begin elapsed result
  echo -n " * $1... " >&3
  shift
  begin=$(date '+%s')
  echo "### $@"
  "$@"
  result=$?
  if [[ $result -eq 0 ]]; then
    echo -n "OK" >&3
  else
    echo -n "fail" >&3
    errors=$[$errors + 1]
  fi
  echo
  elapsed=$(duration $[$(date '+%s') - $begin])
  echo " ($elapsed)" >&3
}

transfer() {
  local extra
  interactive && extra='--progress'
  rsync -e "$RSH" --modify-window=10 -rltzvh $extra "$@"
}

transfer_ask() {
  local dry result answer
  dry=$(transfer -n "$@")
  result=$?
  dry=$(grep -v '^\./$' <<< "$dry")
  echo "$dry"
  [[ $result -ne 0 ]] && return $result
  [[ $(wc -l <<< "$dry") -eq 4 ]] && return 0
  if ! interactive; then
    echo -n "action required, " >&3
    return 0
  fi
  read -p "Continue? [y/N] " answer
  [[ $answer == "y" ]] || return 0
  echo
  transfer "$@"
}

transfer_enc() {
  local key src dest mount result
  key=$1
  src=$2
  dest=$3
  mount=~/.encfs-mnt
  result=0
  mkdir "$mount" || return 1
  encfs --stdinpass --standard --reverse "$src" "$mount" <<< "$key"
  result=$?
  if [[ $result -eq 0 ]]; then
    # Trailing / is important to transfer contents and not directory
    transfer --delete "$mount/" "$dest"
    result=$?
    fusermount -u "$mount"
  fi
  rmdir "$mount"
  return $result
}

check_exists() {
  while [[ -n "$1" ]]; do
    if [[ ! -e "$1" ]]; then
      echo "$1 not available" >&2
      exit 1
    fi
    shift
  done
}

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

if [[ "${BASH_SOURCE[0]}" = "$0" ]]; then
  main "$@"
fi
