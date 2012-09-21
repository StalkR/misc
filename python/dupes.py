#!/usr/bin/python
"""Find duplicate files.

Other programs doing this:
1) fdupes: http://premium.caribe.net/~adrian2/fdupes.html
   under optimized, reads file twice if dup (md5sum, byte by byte)
2) fdup: https://github.com/pozdnychev/fdup/
   under optimized, compare files 2 by 2 (read same file multiple times)

The algorithm I implemented tries to be efficient in term of disk reads
and comparisons:
1) list files (ignore symlink)
2) easy triage with stat operation:
    - files with same path, same dev+inode are duplicates
    - files with different sizes are not duplicates
3) find duplicates by working on a list of disjoint set of files, reading
   by blocks, hashing, comparing all hashes then blocks if necessary
"""

import hashlib
import itertools
import os
import sys


class ProgressClock(object):
  """Simple progress class showing a turning bar /-\|."""

  def __init__(self, message, fp=sys.stderr):
    self.fp = fp
    self.fp.write(message + ' |')
    self.counter = 0

  def Tick(self):
    if self.counter == 0:
      self.fp.write('\b/')
    elif self.counter == 1:
      self.fp.write('\b-')
    elif self.counter == 2:
      self.fp.write('\b\\')
    else:
      self.fp.write('\b|')
    self.counter = (self.counter + 1) % 4

  def End(self):
    self.fp.write('\b \n')


class ProgressPercent(object):
  """Percent progress avancement class."""

  def __init__(self, message, total, fp=sys.stderr):
    self.fp = fp
    self.fp.write(message + ' %3i%%' % 0)
    self.i = 0
    self.total = total
    self.previous = 0

  def Tick(self):
    percent = 100*self.i/self.total
    if percent != self.previous:
      self.fp.write('\b\b\b\b%3i%%' % percent)
      self.previous = percent
    self.i += 1

  def End(self):
    self.fp.write('\b\b\b\b    \n')


class File(object):
  """File representation with helper for stat and comparison."""

  def __init__(self, path):
    self.path = path
    self._stat = None

  @property
  def stat(self):
    if not self._stat:
      self._stat = os.stat(self.path)
    return self._stat

  @property
  def dev_inode(self):
    return self.stat.st_dev, self.stat.st_ino

  @property
  def size(self):
    return self.stat.st_size

  def ObviousDuplicate(self, file2):
    return self.path == file2.path or self.dev_inode == file2.dev_inode

  def PotentialDuplicate(self, file2):
    return self.size == file2.size

  def __eq__(self, other):
    return self.path == other.path

  def __ne__(self, other):
    return self.path != other.path

  def __lt__(self, other):
    return self.path < other.path

  def __le__(self, other):
    return self.path <= other.path

  def __gt__(self, other):
    return self.path > other.path

  def __ge__(self, other):
    return self.path >= other.path


def ListFiles(path):
  """Return list of files in a path, ignoring symlinks."""
  files = []  # List of File.
  p = ProgressClock('[*] Listing files')
  for dirpath, _, filenames in os.walk(path):
    for filename in filenames:
      p.Tick()
      path = os.path.join(dirpath, filename)
      if os.path.isfile(path) and not os.path.islink(path):
        files.append(File(path))
  p.End()
  return files


class DupeList(object):
  """Class representing a list of duplicates with helpers."""

  def __init__(self, duplist=None):
    # List of disjoint set of Files.
    self.duplist = duplist if duplist else []

  def __repr__(self):
    return 'DupeList(%s)' % repr(self.duplist)

  def __len__(self):
    return len(self.duplist)

  def __iter__(self):
    return self.duplist.__iter__()

  def Insert(self, a_set):
    for dupset in self.duplist:
      if dupset.intersection(a_set):
        dupset.update(a_set)
        return
    self.duplist.append(a_set)

  def Merge(self, a_duplist):
    for a_dupset in a_duplist:
      self.Insert(a_dupset)

  def AddDup(self, a, b):
    self.Insert(set([a, b]))

  def IsDup(self, element):
    for dupset in self.duplist:
      if element in dupset:
        return True


def FindDups(files, min_size=0, block_size=4096):
  """Find duplicate files in a list of File elements, two passes."""
  work = DupeList()
  # Binomial coefficient C(len(files), 2)
  total = len(files) * (len(files) - 1) / 2
  p = ProgressPercent('[+] Triage obvious dups/non-dups', total)
  for file1, file2 in itertools.combinations(files, 2):
    p.Tick()
    if file1.size < min_size or file2.size < min_size:
      continue
    if not file1.ObviousDuplicate(file2) and file1.PotentialDuplicate(file2):
      work.AddDup(file1, file2)
  p.End()

  dups = DupeList()
  p = ProgressPercent('[+] Find duplicates in same-size files', len(work))
  for fileset in work:
    p.Tick()
    for f in fileset:
      f.fp = open(f.path, 'rb')
    file_size = list(fileset)[0].size
    dups.Merge(SameSizeDups(DupeList([fileset]), file_size, block_size))
    for f in fileset:
      f.fp.close()
  p.End()

  return dups


def SameSizeDups(duplist, file_size, block_size=4096):
  """Takes a duplist of same size File and returns duplist of duplicates."""
  offset = 0
  while len(duplist) and offset < file_size:
    tmplist = DupeList()
    for dupset in duplist:
      for f in dupset:
        block = f.fp.read(block_size)
        f.md5 = hashlib.md5(block).digest()
        f.sha1 = hashlib.sha1(block).digest()
    offset += block_size
    for dupset in duplist:
      for file1, file2 in itertools.combinations(dupset, 2):
        if file1.md5 == file2.md5 and file1.sha1 == file2.sha1:
          tmplist.AddDup(file1, file2)
    duplist = tmplist
  return duplist


def ReportDups(duplist, min_size=0):
  for dupset in duplist:
    if list(dupset)[0].size > min_size:
      print 'Duplicates:'
      for f in sorted(dupset):
        print '  %i: %r' % (f.size, f.path)


def main():
  if len(sys.argv) < 2:
    print 'Usage: %s <path> [min size]' % sys.argv[0]
    raise SystemExit

  path = sys.argv[1]
  min_size = sys.argv[2] if len(sys.argv) > 2 else 0

  files = ListFiles(path)
  dups = FindDups(files, min_size)
  ReportDups(dups, min_size)


if '__main__' == __name__:
  main()
