#!/usr/bin/python
import sys, re, urllib, htmlentitydefs
class R(urllib.FancyURLopener):
  version = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11"

def decode(s):
  s = re.sub("&#([0-9a-fA-F]+);", lambda m: unichr(int(m.group(1))), s)
  s = re.sub("&(\w+?);", lambda m: htmlentitydefs.entitydefs.get(m.group(1), m.group(0)), s)
  return s

def clean(data): # remove html tags, strip & decode htmlencoded chars
  return decode(re.sub(r'<.*?>', '', data).strip())

def geoip(a):
  """Use MaxMind Online Demo to locate an IP/hostname, return a dictionary of results
URL: http://www.maxmind.com/app/locate_demo_ip
Keys: City, ISP, Region, Hostname, Country Code, Longitude, Postal Code,
      Latitude, Organization, Region Name, Country Name, Metro Code, Area Code
Limit: 25 demo lookups per day"""
  params = {"ips": a, "type": "", "u": "", "p": ""}
  url = "http://www.maxmind.com/app/locate_demo_ip"
  p = R().open(url, urllib.urlencode(params)).read().decode("utf-8")
  
  p = p[p.find(" Results"):]
  p = p[p.find("<table>"):]
  p = p[:p.find("</table>")]
  p = p.split("<tr>")[1:]
  if len(p) < 2:
    return {"Error": "no results (25 demo lookups per day limit reached?)"}
  
  h = map(lambda x: clean(x), p[0].split("<th>")[1:])
  r = map(lambda x: clean(x), p[1].split("<td>")[1:])
  
  return dict(zip(h, r))

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print "Usage: %s <IP or hostname>" % sys.argv[0]
    raise SystemExit(1)
  
  g = geoip(sys.argv[1])
  print ", ".join("%s: %s" % (k, g[k]) for k in sorted(g.keys()) if len(g[k]))
