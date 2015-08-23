"""Snappy compression pure python implementation.

The implementation is based on https://github.com/golang/snappy
at commit 723cc1e459b8eea2dea4583200fd60757d40097a."""

class Error(Exception):
  """Base error class for snappy module."""

class ErrorCorrupt(Error):
  """Corrupt input."""

class ErrorTooLarge(Error):
  """Decoded block is too large."""

class ErrorUnsupported(Error):
  """Unsupported input."""

# Each encoded block begins with the varint-encoded length of the decoded data,
# followed by a sequence of chunks. Chunks begin and end on byte boundaries.
# The first byte of each chunk is broken into its 2 least and 6 most
# significant bits called l and m: l ranges in [0, 4) and m ranges in [0, 64).
# l is the chunk tag. Zero means a literal tag. All other values mean a copy
# tag.
#
# For literal tags:
#   - If m < 60, the next 1 + m bytes are literal bytes.
#   - Otherwise, let n be the little-endian unsigned integer denoted by the
#     next m - 59 bytes. The next 1 + n bytes after that are literal bytes.
#
# For copy tags, length bytes are copied from offset bytes ago, in the style of
# Lempel-Ziv compression algorithms. In particular:
#   - For l == 1, the offset ranges in [0, 1<<11) and the length in [4, 12).
#     The length is 4 + the low 3 bits of m. The high 3 bits of m form bits
#     8-10 of the offset. The next byte is bits 0-7 of the offset.
#   - For l == 2, the offset ranges in [0, 1<<16) and the length in [1, 65).
#     The length is 1 + m. The offset is the little-endian unsigned integer
#     denoted by the next 2 bytes.
#   - For l == 3, this tag is a legacy format that is no longer supported.

tagLiteral = 0x00
tagCopy1   = 0x01
tagCopy2   = 0x02
tagCopy4   = 0x03

checksumSize    = 4
chunkHeaderSize = 4
magicBody       = 'sNaPpY'
magicChunk      = '\xff\x06\x00\x00' + magicBody
# https://code.google.com/p/snappy/source/browse/trunk/framing_format.txt says
# that "the uncompressed data in a chunk must be no longer than 65536 bytes".
maxUncompressedChunkLen = 65536

chunkTypeCompressedData   = 0x00
chunkTypeUncompressedData = 0x01
chunkTypePadding          = 0xfe
chunkTypeStreamIdentifier = 0xff

def uint8(n):
  return n & ((1<<8) - 1)

def uint32(n):
  return n & ((1<<32) - 1)

def uint64(n):
  return n & ((1<<64) - 1)

class CRC32(object):
  def __init__(self, polynom):
    table = [0]*256
    for i in range(256):
      fwd = i
      for j in range(8, 0, -1):
        if (fwd & 1) == 1:
          fwd = (fwd >> 1) ^ polynom
        else:
          fwd >>= 1
        table[i] = fwd & 0xffffffff
    self.table = table

  def Update(self, s):
    crc = 0xffffffff
    for c in s:
      crc = (crc >> 8) ^ self.table[(crc ^ ord(c)) & 0xff]
    return crc ^ 0xffffffff

castagnoli = CRC32(0x82F63B78)

def crc(b):
  """crc implements the checksum specified in section 3 of
  https://code.google.com/p/snappy/source/browse/trunk/framing_format.txt"""
  r = castagnoli.Update(b)
  return uint32((r>>15|r<<17) + 0xa282ead8)

def uvarint(buf):
  """uvarint decodes a uint64 from buf and returns that value and the number of
  bytes read (> 0). If an error occurred, the value is 0 and the number of
  bytes n is <= 0 meaning:
    n == 0: buf too small
    n  < 0: value larger than 64 bits (overflow)
            and -n is the number of bytes read"""
  x, s = 0, 0
  for i in range(len(buf)):
    b = ord(buf[i])
    if b < 0x80:
      if i > 9 or (i == 9 and b > 1):
        return 0, -(i + 1)  # overflow
      return x | uint64(b) << s, i + 1
    x |= uint64(b&0x7f) << s
    s += 7
  return 0, 0

def putuvarint(x):
  """putuvarint encodes a uint64."""
  buf = []
  while x >= 0x80:
    buf.append(uint8(x) | 0x80)
    x >>= 7
  buf.append(x)
  return ''.join(chr(c) for c in buf)

def decodedLen(src):
  """decodedLen returns the length of the decoded block and the number of bytes
  that the length header occupied."""
  v, n = uvarint(src)
  if n <= 0 or v > 0xffffffff:
    raise ErrorCorrupt
  if v > 0x7fffffff:
    raise ErrorTooLarge
  return v, n

def decompress(buf):
  """decompress returns the decompressed form of buf."""
  dLen, s = decodedLen(buf)
  src = [ord(c) for c in buf]
  dst = [0]*dLen
  d, offset, length = 0, 0, 0
  while s < len(src):
    b = src[s] & 0x03
    if b == tagLiteral:
      x = src[s] >> 2
      if x < 60:
        s += 1
      elif x == 60:
        s += 2
        if s > len(src):
          raise ErrorCorrupt
        x = src[s-1]
      elif x == 61:
        s += 3
        if s > len(src):
          raise ErrorCorrupt
        x = src[s-2] | (src[s-1] << 8)
      elif x == 62:
        s += 4
        if s > len(src):
          raise ErrorCorrupt
        x = src[s-3] | (src[s-2] << 8) | (src[s-1] << 16)
      elif x == 63:
        s += 5
        if s > len(src):
          raise ErrorCorrupt
        x = src[s-4] | (src[s-3] << 8) | (src[s-2] << 16) | (src[s-1] << 24)
      length = x + 1
      if length <= 0:
        raise Error('Unsupported literal length')
      if length > len(dst)-d or length > len(src)-s:
        raise ErrorCorrupt
      dst = dst[:d] + src[s:s+length] + dst[d+length:]
      d += length
      s += length
      continue

    elif b == tagCopy1:
      s += 2
      if s > len(src):
        raise ErrorCorrupt
      length = 4 + ((src[s-2]>>2)&0x7)
      offset = ((src[s-2]&0xe0)<<3) | src[s-1]

    elif b == tagCopy2:
      s += 3
      if s > len(src):
        raise ErrorCorrupt
      length = 1 + (src[s-3]>>2)
      offset = src[s-2] | (src[s-1]<<8)

    elif b == tagCopy4:
      raise Error('Unsupported COPY_4 tag')

    end = d + length
    if offset > d or end > len(dst):
      raise ErrorCorrupt
    while d < end:
      dst[d] = dst[d-offset]
      d += 1

  if d != dLen:
    raise ErrorCorrupt
  return ''.join(chr(c) for c in dst[:d])

maxOffset = 1 << 15

def emitLiteral(lit):
  """emitLiteral returns a literal chunk."""
  n = len(lit) - 1
  dst = []
  if n < 60:
    dst.append((uint8(n)<<2) | tagLiteral)
  elif n < (1<<8):
    dst.append((60<<2) | tagLiteral)
    dst.append(uint8(n))
  elif n < (1<<16):
    dst.append((61<<2) | tagLiteral)
    dst.append(uint8(n))
    dst.append(uint8(n >> 8))
  elif n < (1<<24):
    dst.append((62<<2) | tagLiteral)
    dst.append(uint8(n))
    dst.append(uint8(n >> 8))
    dst.append(uint8(n >> 16))
  elif uint64(n) < (1<<32):
    dst.append((63<<2) | tagLiteral)
    dst.append(uint8(n))
    dst.append(uint8(n >> 8))
    dst.append(uint8(n >> 16))
    dst.append(uint8(n >> 24))
  else:
    raise Error("Source buffer is too long")
  dst.extend(lit)
  return dst

def emitCopy(offset, length):
  """emitCopy writes a copy chunk and returns the number of bytes written."""
  dst = []
  while length > 0:
    x = length - 4
    if 0 <= x and x < (1<<3) and offset < (1<<11):
      dst.append(((uint8(offset>>8)&0x07)<<5) | (uint8(x)<<2) | tagCopy1)
      dst.append(uint8(offset))
      break

    x = length
    if x > (1<<6):
      x = 1 << 6
    dst.append((uint8(x-1)<<2) | tagCopy2)
    dst.append(uint8(offset))
    dst.append(uint8(offset >> 8))
    length -= x
  return dst

def compress(buf):
  """compress returns the compressed form of buf."""
  src = [ord(c) for c in buf]

  # The block starts with the varint-encoded length of the decompressed bytes.
  dst = [ord(c) for c in putuvarint(len(src))]

  # Return early if src is short.
  if len(src) <= 4:
    if len(src) != 0:
      dst.extend(emitLiteral(src))
    return dst

  # Initialize the hash table. Its size ranges from 1<<8 to 1<<14 inclusive.
  maxTableSize = 1 << 14
  shift, tableSize = 32-8, 1<<8
  while tableSize < maxTableSize and tableSize < len(src):
    shift -= 1
    tableSize *= 2
  table = [0]*maxTableSize

  # Iterate over the source bytes.
  s = 0    # The iterator position.
  t = 0    # The last position with the same hash as s.
  lit = 0  # The start position of any pending literal bytes.
  while s+3 < len(src):
    # Update the hash table.
    b0, b1, b2, b3 = src[s], src[s+1], src[s+2], src[s+3]
    h = uint32(b0) | (uint32(b1)<<8) | (uint32(b2)<<16) | (uint32(b3)<<24)
    p = uint32(h*0x1e35a7bd)>>shift
    # We need to to store values in [-1, inf) in table. To save
    # some initialization time, (re)use the table's zero value
    # and shift the values against this zero: add 1 on writes,
    # subtract 1 on reads.
    t, table[p] = table[p]-1, s+1
    # If t is invalid or src[s:s+4] differs from src[t:t+4], accumulate a literal byte.
    if t < 0 or s-t >= maxOffset or b0 != src[t] or b1 != src[t+1] or b2 != src[t+2] or b3 != src[t+3]:
      s += 1
      continue
    # Otherwise, we have a match. First, emit any pending literal bytes.
    if lit != s:
      dst.extend(emitLiteral(src[lit:s]))
    # Extend the match to be as long as possible.
    s0 = s
    s, t = s+4, t+4
    while s < len(src) and src[s] == src[t]:
      s += 1
      t += 1
    # Emit the copied bytes.
    dst.extend(emitCopy(s-t, s-s0))
    lit = s

  # Emit any final pending literal bytes and return.
  if lit != len(src):
    dst.extend(emitLiteral(src[lit:]))
  return ''.join(chr(c) for c in dst)
