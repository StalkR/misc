#!/usr/bin/python
# Maxmind GeoIP lookup via web demo (max 25 lookups).
import json
import sys
import urllib


class UrlOpener(urllib.FancyURLopener):
  version = ('Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.11) '
             'Gecko/20071127 Firefox/2.0.0.11')


def GeoIp(ip):
  """Send request and return dict result from json."""
  url = 'http://www.maxmind.com/geoip/city_isp_org/%s?demo=1'
  js = UrlOpener().open(url % ip).read()
  try:
    return json.loads(js)
  except ValueError:
    return {'error': js}


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print "Usage: %s <IP>" % sys.argv[0]
    raise SystemExit(1)

  result = GeoIp(sys.argv[1])
  nice = []
  for key in sorted(result.keys()):
    if result[key]:
      nice.append('%s: %s' % (key, result[key]))
  print ', '.join(nice)
