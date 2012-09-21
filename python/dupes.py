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
3) find duplicates by working on a list of disjoint set of files, comparing N
   potential duplicates at the same time
"""

import itertools
import os
import sys


class ProgressClock(object):
  """A simple progress class showing a turning bar /-\|."""

  def __init__(self, message, fp=sys.stderr):
    self.fp = fp
    self.fp.write(message + '  ')
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


class ProgressMessage(object):
  """A simple progress class showing a message on a line."""

  def __init__(self, message, fp=sys.stderr):
    self.fp = fp
    self.fp.write(message + '\n')

  def Tick(self, message):
    self.fp.write('\r%s' % message)

  def End(self):
    self.fp.write('\r' + ' '*80 + '\r')


class File(object):
  """This object represents a file and provides SameAs for comparison."""

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


def ListFiles(path):
  files = []  # List of File.
  p = ProgressClock('[*] Listing files')
  for dirpath, _, filenames in os.walk(path):
    p.Tick()
    for filename in filenames:
      path = os.path.join(dirpath, filename)
      if os.path.isfile(path):
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


def FindDups(files, block=4096):
  """Find duplicate files in a list of File elements, two passes."""
  dups = DupeList()
  work = DupeList()

  p = ProgressMessage('[*] First pass, triage obvious dups and not dups')
  # Binomial coefficient C(len(files), 2)
  total = len(files) * (len(files) - 1) / 2
  i = 0
  for file1, file2 in itertools.combinations(files, 2):
    p.Tick('%3i%% [%i/%i]' % (100*i/total, i, total))
    if file1.ObviousDuplicate(file2):
      dups.AddDup(file1, file2)
    elif file1.PotentialDuplicate(file2):
      work.AddDup(file1, file2)
    i += 1
  p.End()

  p = ProgressMessage('[*] Second pass, find duplicates in same-size files')
  total = len(work)
  i = 0
  for fileset in work:
    p.Tick('%3i%% [%i/%i] %i dups' % (100*i/total, i, total, len(dups)))
    for f in fileset:
      f.fp = open(f.path, 'rb')
    dups.Merge(FindDupsRecurse(DupeList([fileset]), 0, block))
    for f in fileset:
      f.fp.close()
  p.End()

  return dups


def FindDupsRecurse(duplist, offset=0, block=4096):
  """Takes a duplist of File elements and returns a sub duplist of these."""
  if not len(duplist):
    return []
  if all([offset >= f.size for dupset in duplist for f in dupset]):
    return duplist
  sublist = DupeList()
  for dupset in duplist:
    for f in dupset:
      f.block = f.fp.read(block) if offset < f.size else True
  for dupset in duplist:
    for file1, file2 in itertools.combinations(dupset, 2):
      if file1.block == file2.block:
        sublist.AddDup(file1, file2)
  return FindDupsRecurse(sublist, offset+block, block)


def ReportDups(duplist, min_size=4096):
  for dupset in duplist:
    if list(dupset)[0].size > min_size:
      print 'Duplicates:'
      for f in dupset:
        print '  %i: %r' % (f.size, f.path)


def main():
  if len(sys.argv) < 2:
    print 'Usage: %s <path>' % sys.argv[0]
    raise SystemExit

  files = ListFiles(sys.argv[1])
  dups = FindDups(files)
  ReportDups(dups)

if '__main__' == __name__:
  main()
