#!/usr/bin/python
"""Replace a python compiled .pyc with another .py(c).

# Create test.pyc that prints test
$ echo "print 'test'" > test.py
$ python -c 'import test'
test

# Create hijacked.pyc that prints hijacked
$ echo "print 'hijacked'" > hijacked.py
$ python -c 'import hijacked'
hijacked

# Replace test.pyc with hijacked.pyc
$ python pyc_replace.py test.pyc hijacked.pyc

# test.pyc successfully replaced
$ python -c 'import test'
hijacked

-- StalkR
"""
import os
import sys
import py_compile

def replace(dest, src):
  head = open(dest,"rb").read(8)
  content = open(src,"rb").read()
  open(dest,"wb").write(head + content[8:])

if __name__=='__main__':
  if len(sys.argv) < 3:
    print "Usage: %s <pyc to replace> <source py(c)>" % sys.argv[0]
    raise SystemExit(1)
  
  dest, src = sys.argv[1], sys.argv[2]
  # if given a .py, first compile it to have a .pyc
  if src.endswith(".py"):
    py_compile.compile(src)
    replace(dest, src + "c")
    os.remove(src + "c")
  else:
    replace(dest, src)
