#!/bin/bash
# Cron to update twitter-db
#   25 3 * * * cd /home/stalkr/twitter-db; flock -nox lock bash -c './db.sh > log 2>&1'
# Ensure you already performed OAuth authentication before:
#   twitter-archiver -o -a; twitter-follow -o -a
# -- StalkR

# Your username + directory to work in
ME=stalkr_
DIR=~/twitter-db

error() { echo "Error: $@" >&2; exit 1; }
cd "$DIR" || error "unable to cd to $DIR"
S=$(date '+%s')

# Save following/followers
twitter-follow -o -g "$ME" > following.lst
twitter-follow -o -r "$ME" > followers.lst

# Archive all tweets of self + following/followers + others
mkdir -p all || error "failed mkdir all"
{
  echo "$ME"
  cat following.lst followers.lst others.lst 2>/dev/null
} | twitter-archiver -o -s "$PWD/all" -- -

# Build subsets of following/followers using symlinks
rm -rf following followers
mkdir following followers || error "failed mkdir following followers"
while read N; do
  [ -f "all/$N" ] && ln -s "../all/$N" "following/$N"
done < following.lst
while read N; do
  [ -f "all/$N" ] && ln -s "../all/$N" "followers/$N"
done < followers.lst

# Rebuild timeline by sorting all following tweets
find following -not -type d -print0 | xargs -0 cat | sort -n > timeline

# Execution time
D=$[$(date '+%s') - $S]
[ -x "$(command -v duration)" ] && D=$(duration $D) || D="${D}s"
echo "Total time: $D"
