"""Unit tests for Snappy compression pure python implementation.

Compare with https://github.com/andrix/python-snappy which are bindings
on top of the C++ implementation https://code.google.com/p/snappy/."""

import random
import snappy
import snappy_pure
import unittest

def randBytes(n):
  with open('/dev/urandom', 'r') as f:
    return f.read(n)

class TestDecode(unittest.TestCase):

  def testFile(self):
    data = open('/etc/passwd', 'r').read()
    compressed = snappy.compress(data)
    if data != snappy.decompress(compressed):
      raise AssertionError('C++ implementation faulty')
    if data != snappy_pure.decompress(compressed):
      raise AssertionError('Python implementation faulty')

  def testRandom(self):
    data = randBytes(random.randint(1, 1<<20))  # 1B to 1 MB
    compressed = snappy.compress(data)
    if data != snappy.decompress(compressed):
      raise AssertionError('C++ implementation faulty')
    if data != snappy_pure.decompress(compressed):
      raise AssertionError('Python implementation faulty')

if __name__ == '__main__':
  unittest.main()
