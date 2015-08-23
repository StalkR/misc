"""Unit tests for Snappy compression pure python implementation.

Rather than copying the tests at https://github.com/golang/snappy we just make
sure we can compress/decompress against the reference bindings.

Snappy reference implementation in C++: https://code.google.com/p/snappy/
Python bindings: https://github.com/andrix/python-snappy
"""

import random
import snappy
import snappy_pure
import unittest


def randBytes(n):
  with open('/dev/urandom', 'r') as f:
    return f.read(n)


class TestDecompress(unittest.TestCase):

  def testFile(self):
    want = open('/etc/passwd', 'r').read()
    got = snappy_pure.decompress(snappy.compress(want))
    if got != want:
      raise AssertionError('got %r, want %r' % (got, want))

  def testRandom(self):
    want = randBytes(random.randint(1, 1<<20))  # 1B to 1 MB
    got = snappy_pure.decompress(snappy.compress(want))
    if got != want:
      raise AssertionError('got %r, want %r' % (got, want))


class TestCompress(unittest.TestCase):

  def testFile(self):
    want = open('/etc/passwd', 'r').read()
    got = snappy.decompress(snappy_pure.compress(want))
    if got != want:
      raise AssertionError('got %r, want %r' % (got, want))

  def testRandom(self):
    want = randBytes(random.randint(1, 1<<20))  # 1B to 1 MB
    got = snappy.decompress(snappy_pure.compress(want))
    if got != want:
      raise AssertionError('got %r, want %r' % (got, want))


if __name__ == '__main__':
  unittest.main()
