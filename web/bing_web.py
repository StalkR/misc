#!/usr/bin/python
# Bing search via Web because simpler than their !@# azure API.

import sys, re, urllib, htmlentitydefs
class R(urllib.FancyURLopener):
  version = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11"

def decode(s):
  s = s.replace('&nbsp;', ' ')
  s = re.sub("&#([0-9a-fA-F]+);", lambda m: unichr(int(m.group(1))), s)
  s = re.sub("&(\w+?);", lambda m: htmlentitydefs.entitydefs.get(m.group(1), m.group(0)), s)
  return s

def do_web_search(arg, exact=True):
  A = {"SearchResponse": {"Web": {}}}
  
  params = {"q": ("+" if exact else "") + arg}
  url = "http://www.bing.com/search?%s" % urllib.urlencode(params)
  p = R().open(url).read().decode("utf-8")

  if '<div id="no_results">' in p:
    A["SearchResponse"]["Web"]["Total"] = 0
    A["SearchResponse"]["Web"]["Results"] = []
    return A

  results = p.replace('&#160;', '').replace(',', '')
  c = re.search("id=\"count\">([0-9]*) [^<]+</span>", results)
  if not c:
    return "Cannot parse total results"
  A["SearchResponse"]["Web"]["Total"] = int(c.group(1))
  
  m = re.search("<div id=\"results\">.*</div>", p, re.DOTALL)
  if not m:
    return "Cannot parse results"
  
  A["SearchResponse"]["Web"]["Results"] = []
  for e in m.group(0).split("<li class=\"sa_wr\">")[1:]:
    r = {}
    e = re.sub("</?strong>", "", e)
  
    url = re.search(">([^<]*)</cite>", e)
    if not url:
      return "Cannot parse url in result: %s" % repr(e)
    r["Url"] = decode(url.group(1))
    if "//" not in r["Url"]: r["Url"] = "http://"+r["Url"]
  
    title = re.search(">([^<]*)</a>", e)
    if not title:
      return "Cannot parse title in result: %s" % repr(e)
    r["Title"] = decode(title.group(1))
    
    description = re.search("<p>(.*?)</p>", e)
    if description:
      r["Description"] = decode(description.group(1))
    
    A["SearchResponse"]["Web"]["Results"].append(r)
  
  return A

def search(arg, limit=130, exact=True, f=None):
  u = urllib.urlencode({"q":arg})
  more = "http://www.bing.com/search?%s http://www.google.com/search?%s" % (u,u)
  if not len(arg):
    print "No search term?"
    return
  q = f(arg, exact=exact)
  if "SearchResponse" not in q or "Web" not in q["SearchResponse"]:
    print "Error: %s" % repr(q)[:150]
    print "More: %s" % more
  else:
    w = q["SearchResponse"]["Web"]
    if w["Total"] == 0:
        print "No result - %s" % more
    else:
      for i,r in enumerate(w["Results"]):
        d = [r["Url"], r["Title"]]
        if "Description" in r:
          d.append(r["Description"])
        m = "%2i. %s" % (i+1, " - ".join(d))
        print m[:limit-3]+"..." if len(m)>limit else m
      print "%i results - More: %s" % (w["Total"], more)

if __name__ == "__main__":
  search(" ".join(sys.argv[1:]), f=do_web_search)
