#!/usr/bin/python
"""Find duplicate files.

Other programs doing this:
1) fdupes: http://premium.caribe.net/~adrian2/fdupes.html
2) fdup: https://github.com/pozdnychev/fdup/

1) and 2) are in C, so quite optimized, but it also means you need to compile
it. 1) needs to compute the md5sum, which means reading the file entirely when
it can be avoided if the first bytes are different.

This version is like 2) in that it directly compares files. It's less optimum
because of python, but also easier to run (no compilation needed).
"""

import os
import sys


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

  def SameAs(self, file2, block=4096):
    if self.path == file2.path:
      return True
    elif self.dev_inode == file2.dev_inode:
      return True
    elif self.size != file2.size:
      return False
    else:
      f1 = open(self.path, 'r')
      f2 = open(file2.path, 'r')
      offset = 0
      while offset <= self.size:
        if f1.read(block) != f2.read(block):
          return False
        offset += block
      return True


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


class DupesFinder(object):
  """Class to find duplicate files in a path."""

  def ListFiles(self, path):
    self.list = []  # List of File.
    p = ProgressClock('[*] Listing files')
    for dirpath, _, filenames in os.walk(path):
      p.Tick()
      for filename in filenames:
        path = os.path.join(dirpath, filename)
        if os.path.isfile(path):
          self.list.append(File(path))
    p.End()

  def FindDups(self, min_size=4096):
    self.dups = []  # List of set of File.
    p = ProgressMessage('[*] Finding duplicates')
    size = len(self.list)
    for i in xrange(size - 1):  # Last one already compared with all others.
      p.Tick('%3i%% [%i/%i] %i dups' % (100*i/size, i, size, len(self.dups)))
      file1 = self.list[i]
      if self.IsDup(file1):  # Already analyzed.
        continue
      for file2 in self.list:
        if file1 == file2:
          continue
        if file1.SameAs(file2):
          self.AddDup(file1, file2)
      if self.IsDup(file1) and file1.size > min_size:
        self.ReportDup(file1)
    p.End()

  def IsDup(self, file1):
    for dup in self.dups:
      if file1 in dup:
        return True

  def AddDup(self, file1, file2):
    for dup in self.dups:
      if file1 in dup or file2 in dup:
        dup.update(set([file1, file2]))
        return
    self.dups.append(set([file1, file2]))

  def ReportDup(self, file1):
    sys.stderr.write('\n')
    for dup in self.dups:
      if file1 in dup:
        for phile in dup:
          print '%i: %r' % (phile.size, phile.path)


def FindDups(path, min_size=4096):
  """Method to find and report duplicates in a path."""
  df = DupesFinder()
  df.ListFiles(path)
  df.FindDups(min_size)


def main():
  if len(sys.argv) < 2:
    print 'Usage: %s <path>' % sys.argv[0]
    raise SystemExit

  FindDups(sys.argv[1])


if '__main__' == __name__:
  main()
