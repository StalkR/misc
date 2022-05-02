#!/usr/bin/python3
'''Calculate or view HTTP Public Key Pins.

Requires OpenSSL binary.
RFC draft: https://tools.ietf.org/html/draft-ietf-websec-key-pinning-11

Example with CAcert Root CA (Class 1) certificate:
$ wget https://www.cacert.org/certs/root.crt
$ python http_pins.py root.crt
root.crt:
* SPKI fingerprint (sha256): 6f:28:51:40:9d:71:05:04:a3:51:15:ab:cb:9a:6d:d3:f2:57:7e:c9:37:c9:ef:19:38:92:6f:a8:2f:d6:ff:5d
Public-Key-Pins: max-age=600; pin-sha256="byhRQJ1xBQSjURWry5pt0/JXfsk3ye8ZOJJvqC/W/10="
Warning! Per RFC you need at minimum two pins

$ python http_pins.py byhRQJ1xBQSjURWry5pt0/JXfsk3ye8ZOJJvqC/W/10=
SPKI fingerprint (sha256): 6f:28:51:40:9d:71:05:04:a3:51:15:ab:cb:9a:6d:d3:f2:57:7e:c9:37:c9:ef:19:38:92:6f:a8:2f:d6:ff:5d
'''

import base64
import binascii
import hashlib
import os
import string
import subprocess
import sys

def extract_spki(cert):
  '''Obtain SubjectPublicKeyInfo from public certificate using OpenSSL.'''
  args = ['openssl', 'x509', '-pubkey', '-noout', '-in', cert]
  proc = subprocess.Popen(args, stdout=subprocess.PIPE)
  out = proc.communicate()[0].strip().split(b'\n')
  # remove 1st (BEGIN PUBLIC KEY) and last line (END PUBLIC KEY)
  return base64.b64decode(b''.join(map(bytes.strip, out[1:-1])))

def pin_to_fingerprint(pin):
  return ':'.join('%.2x' % c for c in base64.b64decode(pin))

def fingerprint_to_pin(fingerprint):
  return base64.b64encode(bytes.fromhex(fingerprint.replace(':', ''))).strip()

def fingerprint(spki, hash):
  '''Calculate fingerprint of a SubjectPublicKeyInfo given a hash function.'''
  return ':'.join('%.2x' % c for c in hash(spki).digest())

def explain_pin(pin):
  '''Explain a pin by showing its fingerprint with hash algorithm.'''
  try:
    fp = pin_to_fingerprint(pin)
  except binascii.Error:
    print('Error: invalid pin (base64 decode failed)')
    return False

  # +1 to have even ':', /3 for hex representation with ':'
  fp_length = (len(fp) + 1) / 3
  if fp_length == 32:
    algo = 'sha256'
  else:
    algo = ''

  if not algo:
    print('Error: unrecognized algorithm ength %i' % fp_length)
    print('SPKI fingerprint: %s' % fp)
    return False

  print('SPKI fingerprint (%s): %s' % (algo, fp))
  return True

def main(args):
  if len(args) < 2:
    print('Usage: %s <cert|pin> [<cert>...]' % args[0])
    return
  
  # Probably not a certificate but a pin, show fingerprint
  if not os.path.exists(args[1]):
    if not explain_pin(args[1]):
      raise SystemExit(1)
  
  # Calculate fingerprints and pins of each certificate
  else:
    pins = []
    for cert in args[1:]:
      if not os.path.exists(cert):
        print('%s: does not exist' % cert)
        continue
      print('%s:' % cert)
      spki = extract_spki(cert)
      fp_sha256 = fingerprint(spki, hashlib.sha256)
      print('* SPKI fingerprint (sha256): %s' % fp_sha256)
      pins.append('pin-sha256="%s"' % fingerprint_to_pin(fp_sha256))

    print('Public-Key-Pins: %s' % '; '.join(['max-age=600'] + pins))
    if len(pins) < 2:
      print('Warning! Per RFC you need at minimum two pins')
    else:
      print('Remember: the secondary pin has to be unrelated (not checked)')

if __name__ == '__main__':
  main(sys.argv)
