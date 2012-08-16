#!/usr/bin/python
# Script to get country of a hostname/IP
# It uses python-geoip bindings and geoip-database
import sys
import GeoIP

# from http://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python
import socket
def is_valid_ipv4_address(address):
    try:
        addr= socket.inet_pton(socket.AF_INET, address)
    except AttributeError: # no inet_pton here, sorry
        try:
            addr= socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error: # not a valid address
        return False
    return True

def is_valid_ipv6_address(address):
    try:
        addr= socket.inet_pton(socket.AF_INET6, address)
    except socket.error: # not a valid address
        return False
    return True

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print "Usage: %s <IP or hostname>" % sys.argv[0]
    raise SystemExit(1)
  
  a = sys.argv[1]
  gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

  if is_valid_ipv4_address(a):
    # not necessary
    #gi = GeoIP.open("/usr/share/GeoIP/GeoIP.dat",GeoIP.GEOIP_STANDARD)
    print "%s (%s)" % (gi.country_name_by_addr(a), gi.country_code_by_addr(a))
  
  elif is_valid_ipv6_address(a):
    #gi = GeoIP.open("/usr/share/GeoIP/GeoIPv6.dat",GeoIP.GEOIP_STANDARD)
    print "Not yet supported by python-geoip bindings"
  
  else:
    print "%s (%s)" % (gi.country_name_by_name(a), gi.country_code_by_name(a))
    # we don't care
    #start,end = gi.range_by_ip(a)
    #print "Range: %s-%s" % (start, end)
