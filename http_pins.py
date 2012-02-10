#!/usr/bin/python
"""Calculate or view HTTP Public Key Pins.

Requires OpenSSL binary.
RFC draft: https://tools.ietf.org/html/draft-ietf-websec-key-pinning-01

Example with CAcert Root CA (Class 1) and Class 3 certificates:
$ wget https://www.cacert.org/certs/root.crt
$ wget https://www.cacert.org/certs/class3.crt
$ python http_pins.py root.crt class3.crt
root.crt:
* SPKI fingerprint (sha1): 10:da:62:4d:ef:41:a3:04:6d:cd:ba:3d:01:8f:19:df:3d:c9:a0:7c
* SPKI fingerprint (sha256): 6f:28:51:40:9d:71:05:04:a3:51:15:ab:cb:9a:6d:d3:f2:57:7e:c9:37:c9:ef:19:38:92:6f:a8:2f:d6:ff:5d
class3.crt:
* SPKI fingerprint (sha1): f0:61:d8:3f:95:8f:4d:78:b1:47:b3:13:39:97:8e:a9:c2:51:ba:9b
* SPKI fingerprint (sha256): bd:0d:07:29:6b:43:fa:e0:3b:64:e6:50:cb:d1:8f:5e:26:71:42:52:03:51:89:d3:e1:26:3e:48:14:b4:da:5a
Public-Key-Pins: max-age=600; pin-sha1=ENpiTe9BowRtzbo9AY8Z3z3JoHw=; pin-sha256=byhRQJ1xBQSjURWry5pt0/JXfsk3ye8ZOJJvqC/W/10=; pin-sha1=8GHYP5WPTXixR7MTOZeOqcJRups=; pin-sha256=vQ0HKWtD+uA7ZOZQy9GPXiZxQlIDUYnT4SY+SBS02lo=

$ python http_pins.py ENpiTe9BowRtzbo9AY8Z3z3JoHw=
SPKI fingerprint (sha1): 10:da:62:4d:ef:41:a3:04:6d:cd:ba:3d:01:8f:19:df:3d:c9:a0:7c

$ python http_pins.py byhRQJ1xBQSjURWry5pt0/JXfsk3ye8ZOJJvqC/W/10=
SPKI fingerprint (sha256): 6f:28:51:40:9d:71:05:04:a3:51:15:ab:cb:9a:6d:d3:f2:57:7e:c9:37:c9:ef:19:38:92:6f:a8:2f:d6:ff:5d

-- StalkR
"""

import binascii
import hashlib
import os
import string
import subprocess
import sys

def extract_spki(cert):
  """Obtain SubjectPublicKeyInfo from public certificate using OpenSSL."""
  args = ["openssl", "x509", "-pubkey", "-noout", "-in", cert]
  proc = subprocess.Popen(args, stdout=subprocess.PIPE)
  out = proc.communicate()[0].split("\n")
  # remove 1st (BEGIN PUBLIC KEY) and last line (END PUBLIC KEY)
  return "".join(map(string.strip, out[1:-1])).decode("base64")

def pin_to_fingerprint(pin):
  return ":".join(c.encode("hex") for c in pin.decode("base64"))

def fingerprint_to_pin(fingerprint):
  return fingerprint.replace(":","").decode("hex").encode("base64").strip()

def fingerprint(spki, hash):
  """Calculate fingerprint of a SubjectPublicKeyInfo given a hash function."""
  return ":".join(c.encode("hex") for c in hash(spki).digest())

def main(args):
  if len(args) < 2:
    print "Usage: %s <cert|pin> [<cert>...]" % args[0]
    return
  
  # Probably not a certificate but a pin, show fingerprint
  if not os.path.exists(args[1]):
    try:
      fp = pin_to_fingerprint(args[1])
    except binascii.Error:
      print "Error: invalid pin (base64 decode failed)"
      raise SystemExit(1)
    
    # +1 to have even ":", /3 to ignore ":" and hex
    fp_length = (len(fp) + 1) / 3
    hash_func = None
    if fp_length == 20:
      hash_func = "sha1"
    elif fp_length == 32:
      hash_func = "sha256"
    
    if hash_func:
      print "SPKI fingerprint (%s): %s" % (hash_func, fp)
    else:
      print "Error: invalid length (%i is not sha1 or sha256)" % fp_length
      print "SPKI fingerprint: %s" % fp
      raise SystemExit(1)
  
  # Calculate fingerprints and pins of each certificate
  else:
    pins = [ "max-age=600" ]
    for cert in args[1:]:
      print "%s:" % cert
      spki = extract_spki(cert)
      fp_sha1 = fingerprint(spki, hashlib.sha1)
      fp_sha256 = fingerprint(spki, hashlib.sha256)
      print "* SPKI fingerprint (sha1): %s" % fp_sha1
      print "* SPKI fingerprint (sha256): %s" % fp_sha256
      pins.append("pin-sha1=%s" % fingerprint_to_pin(fp_sha1))
      pins.append("pin-sha256=%s" % fingerprint_to_pin(fp_sha256))
    print "Public-Key-Pins: %s" % "; ".join(pins)

if __name__=='__main__':
  main(sys.argv)
