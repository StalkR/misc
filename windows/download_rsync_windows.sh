#!/bin/bash
# Download a self-contained rsync.exe build for Windows from https://msys2.org

MSYS_URL='https://repo.msys2.org/msys/x86_64/'

msys=$(curl -s "$MSYS_URL")

curl -so x "${MSYS_URL}$(sed -n 's/<a href="\(msys2-runtime-[0-9].*\.zst\)">.*/\1/p' <<< "$msys" | tail -1)"
tar --strip-components=2 -I zstd -xvf x usr/bin/msys-2.0.dll

curl -so x "${MSYS_URL}$(sed -n 's/<a href="\(libopenssl-[0-9].*\.zst\)">.*/\1/p' <<< "$msys" | tail -1)"
tar --strip-components=2 -I zstd -xvf x usr/bin/msys-crypto-3.dll

curl -so x "${MSYS_URL}$(sed -n 's/<a href="\(libiconv-[0-9].*\.zst\)">.*/\1/p' <<< "$msys" | tail -1)"
tar --strip-components=2 -I zstd -xvf x usr/bin/msys-iconv-2.dll

curl -so x "${MSYS_URL}$(sed -n 's/<a href="\(liblz4-[0-9].*\.zst\)">.*/\1/p' <<< "$msys" | tail -1)"
tar --strip-components=2 -I zstd -xvf x usr/bin/msys-lz4-1.dll

curl -so x "${MSYS_URL}$(sed -n 's/<a href="\(libxxhash-[0-9].*\.zst\)">.*/\1/p' <<< "$msys" | tail -1)"
tar --strip-components=2 -I zstd -xvf x usr/bin/msys-xxhash-0.dll

curl -so x "${MSYS_URL}$(sed -n 's/<a href="\(libzstd-[0-9].*\.zst\)">.*/\1/p' <<< "$msys" | tail -1)"
tar --strip-components=2 -I zstd -xvf x usr/bin/msys-zstd-1.dll

curl -so x "${MSYS_URL}$(sed -n 's/<a href="\(rsync-[0-9].*\.zst\)">.*/\1/p' <<< "$msys" | tail -1)"
tar --strip-components=2 -I zstd -xvf x usr/bin/rsync.exe

rm -f x
