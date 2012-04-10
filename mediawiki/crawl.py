#!/usr/bin/env python2.6
# Wikitools from http://code.google.com/p/python-wikitools/
from wikitools import *
import re, os
from urllib import unquote
from sys import argv

followed = []
prefix = argv[1] if len(argv) > 1 else '.'

def title_to_file(title, attachment = False):
  title = title.replace('/','-').replace(':',os.sep).split('#')[0]
  return prefix + os.sep + title + ('' if attachment else '.txt')

def save(title, text):
  file = title_to_file(title)
  print "Saving page %s in %s" % (repr(title), repr(file))
  try:
    os.makedirs(os.path.dirname(file))
  except OSError, e:
    pass
  open(file,'w').write(text)

def get(N, title): # recursive
  global followed

  if len(title) == 0 or title in followed:
    return

  file = title_to_file(title)
  text = ''
  if os.path.exists(file):
    print "Already got %s" % repr(title)
    text = open(file, 'r').read() # to allow resume
  else:
    try:
      text = page.Page(N,title).getWikiText()
      save(title, text)
    except page.NoPage, e:
      print "No such page %s" % repr(title)
      return

  followed.append(title)

  for t in re.findall('\[\[([^|\]]*)',text):
    get(N,unquote(t))
    if t.lower().startswith(("image:", "file:")):
      try: # attachments
        wikifile.File(N, t).download(location=title_to_file(t, True))
        print "Download %s -> OK" % repr(t)
      except Exception,e:
        print "Download %s -> FAILED" % repr(t)

def credentials(filename):
  try:
    user, password = open(filename).read().strip().split('\n', 1)
  except IOError, e:
    print "Cannot open credentials %s" % repr(filename)
    raise SystemExit(1)
  except ValueError, e:
    print "Cannot parse credentials, format <user>\n<pass>"
  return user, password

if __name__ == '__main__':
  N = wiki.Wiki(url="https://wiki.url/api.php")
  N.login(*credentials("userpass.txt"))
  get(N,'Main_Page')

