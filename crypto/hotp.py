#!/usr/bin/env python
"""HOTP RFC 4226 client.

Configuration

  If you get a QRCode, decode it to have an otpauth URL with the values:
      otpauth://hotp/xxx?secret=<secret>&counter=<counter>

  Then save the values, e.g.:
    $ echo PB4HQ6DYPB4HQ6DYPB4HQ6DYPB4HQ6DY > ~/.otp_secret
    $ echo 0 > ~/.otp_counter

  Note: if you do not know your HOTP parameters, you can try to ask for a
  new configuration.


Usage

  To get the current value of the OTP:
    $ python hotp.py
    264621

  Note that this does not increase the counter, to increase it after:
    $ python hotp.py --update
    264621
    $ python hotp.py
    668014


Help

  usage: hotp.py [-h] [--update] [--digits DIGITS] [--secret SECRET]
                      [--counter COUNTER]
  
  HOTP RFC 4226 client.
  
  optional arguments:
    -h, --help         show this help message and exit
    --update           Update counter in the end. (default: False)
    --digits DIGITS    Number of digits of the OTP. (default: 6)
    --secret SECRET    Location of secret (20 bytes or base32 format). (default:
                       ~/.otp_secret)
    --counter COUNTER  Location of counter. (default: ~/.otp_counter)


Requirements

  python-argparse
  Tested with python2.6.


-- StalkR
"""
import argparse
import base64
import hmac
import hashlib
import os
import struct
import sys

DIGEST = hashlib.sha1

def hotp(key, counter, digits=6):
  """RFC 4226 HOTP: key 20-bytes string, counter unsigned long long."""
  assert(type(key) is str and len(key) == 20)
  assert(type(counter) is int and 0 <= counter < 2**64)
  hashed = hmac.new(key, struct.pack('>Q', counter), DIGEST).digest()
  offset = ord(hashed[-1]) & 0xF
  truncatedHash = struct.unpack('>L', hashed[offset:][:4])[0] & 0x7FFFFFFF
  pinValue = truncatedHash % 10**digits
  return '%06i' % pinValue

def parse_args():
  """Parse the command line arguments."""
  parser = argparse.ArgumentParser(
      description = 'HOTP RFC 4226 client.',
      add_help = True,
      formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--update', action='store_true', default=False,
                      help='Update counter in the end.')
  parser.add_argument('--digits', type=int, default=6,
                      help='Number of digits of the OTP.')
  parser.add_argument('--secret', type=str, default='~/.otp_secret',
                      help='Location of secret (20 bytes or base32 format).')
  parser.add_argument('--counter', type=str, default='~/.otp_counter',
                      help='Location of counter.')

  args = parser.parse_args()
  args.secret = os.path.expanduser(args.secret)
  args.counter = os.path.expanduser(args.counter)
  return args

def main():
  """Entry point."""
  args = parse_args()

  try:
    secret = open(args.secret).read()
    counter = int(open(args.counter).read().strip())
  except IOError, error:
    print error
    print 'Error opening secret and/or counter file. Have you configured?'
    return 1

  if len(secret) == DIGEST().digest_size:  # 20
    key = secret
  else:  # otpauth://hotp/xxx?secret=<base32 secret>
    key = base64.b32decode(secret.strip())

  print hotp(key, counter, args.digits)

  if args.update:
    try:
      open(args.counter, 'w').write('%i\n' % (counter + 1))
    except IOError, error:
      print error
      print 'Error saving new counter.'
      return 1

  return 0

if __name__ == '__main__':
  sys.exit(main())