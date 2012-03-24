#!/usr/bin/env python
"""YubiKey screen unlocker: unlock your screen using a YubiKey.


Configuration

  To use the program you must first configure a YubiKey in OATH-HOTP mode
  with a secret shared with the host in ~/.yubiunlock. Do this with:

    $ python yubiunlock.py --configure
    Token configured.


Usage

  Run the program, it stays here and wait:

    $ python yubiunlock.py
    Program started, waiting for events.

  Lock your screen and insert the same YubiKey. The program tries to identify
  the token with a challenge-response. If successfull, the program kills your
  screensaver (by default, 'gnome-screensaver') which unlocks your screen:

    $ python yubiunlock.py
    Program started, waiting for events.
    2012-03-24T20:18:29+01:00 Unlocked screen.


Help

  $ python yubiunlock.py -h
  usage: yubiunlock.py [-h] [--debug] [--configure] [--slot SLOT]
                     [--secret SECRET] [--interval INTERVAL] [--daemon]
                     [--screensaver SCREENSAVER]

  YubiKey screen unlocker.

  optional arguments:
    -h, --help            show this help message and exit
    --debug               Enable debug operation (default: False)
    --configure           Configure token (default: False)
    --slot SLOT           Configuration slot to use (default: 1)
    --secret SECRET       Location of shared secret file. (default:
                          ~/.yubiunlock)
    --interval INTERVAL   Polling interval to check for token (default: 1)
    --daemon              Send program to background (default: False)
    --screensaver SCREENSAVER
                          Name of screensaver process to kill (default: gnome-
                          screensaver)


Requirements

  python-argparse, python-daemon, python-psutil, python-usb
  and python-yubico from https://github.com/Yubico/python-yubico

  Tested with python2.6 and YubiKey 2.2.3.


-- StalkR
"""
import argparse
import daemon
import hashlib
import hmac
import os
import psutil
import random
import sys
import time
import usb
import yubico

def hotp(secret, counter, hash=hashlib.sha1):
  """Generic HOTP algorithm, secret/counter are strings."""
  return hmac.new(secret, counter, hash).digest()

def randchar():
  return chr(random.randint(0, 255))

def randstring(size):
  return ''.join(randchar() for _ in range(size))

def date():
  """Date in RFC3339 format."""
  tz = time.strftime('%z')
  return time.strftime('%Y-%m-%dT%H:%M:%S') + tz[:3] + ':' + tz[3:]

def parse_args():
  """Parse the command line arguments."""
  parser = argparse.ArgumentParser(
      description = 'YubiKey screen unlocker.',
      add_help = True,
      formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--debug', action='store_true', default=False,
                      help='Enable debug operation')
  parser.add_argument('--configure', action='store_true', default=False,
                      help='Configure token')
  parser.add_argument('--slot', type=int, default=1,
                      help='Configuration slot to use')
  parser.add_argument('--secret', type=str, default='~/.yubiunlock',
                      help='Location of shared secret file.')
  parser.add_argument('--interval', type=float, default=1,
                      help='Polling interval to check for token')
  parser.add_argument('--daemon', action='store_true', default=False,
                      help='Send program to background')
  parser.add_argument('--screensaver', type=str, default='gnome-screensaver',
                      help='Name of screensaver process to kill')

  args = parser.parse_args()
  args.secret = os.path.expanduser(args.secret)
  return args

def configure(args):
  """Configure token and save secret in file."""
  secret = randstring(20)

  try:
    YK = yubico.find_yubikey()
    Cfg = YK.init_config()
    Cfg.mode_challenge_response(secret, type='HMAC', variable=True,
                                require_button=False)
    Cfg.extended_flag('SERIAL_API_VISIBLE', True)
    YK.write_config(Cfg, slot=args.slot)
  except yubico.yubikey.YubiKeyError, error:
    print 'Configuration failed: %s' % str(error)
    return 1
  except yubico.yubikey_usb_hid.YubiKeyUSBHIDError, error:
    print 'Configuration failed: %s' % str(error)
    return 1

  # success, save secret
  try:
    open(args.secret, 'w').write(secret)
  except IOError, error:
    print 'Unable to create secret file: %s' % str(error)
    return 1

  # try to enforce only user permissions
  try:
    os.chmod(args.secret, 0600)
  except OSError:
    pass

  print 'Token configured.'
  return 0

def tokens():
  """Iterate over all available tokens."""
  for skip in range(256):
    try:
      yield yubico.find_yubikey(skip=skip)
    except yubico.yubikey.YubiKeyError:
      pass
    except usb.USBError:
      pass

def authentify(YK, secret, slot):
  """Authentify token with challenge-response."""
  challenge = randstring(63)
  expected = hotp(secret, challenge)

  try:
    response = YK.challenge_response(challenge, slot=slot)
    if response == expected:
      return True
  except yubico.yubikey.YubiKeyError:
    pass
  except usb.USBError:
    pass

  return False

def screensaver(name):
  """Return screensaver process if found or None."""
  for process in psutil.process_iter():
    if process.name == name:
      return process
  return None

def loop(args, secret):
  """Unlock screen when locked and token present."""
  p = None
  while True:
    # wait for screensaver
    while not p:
      p = screensaver(args.screensaver)
      if p:
        break
      time.sleep(args.interval)
    # wait for token
    while True:
      # we lost screensaver, go back find it
      if not p.is_running():
        p = None
        break
      # try to authenticate all available tokens
      for YK in tokens():
        if authentify(YK, secret, args.slot):
          print '%s Unlocked screen.' % date()
          p.kill()
      time.sleep(args.interval)

def main():
  args = parse_args()

  if args.configure:
    return configure(args)

  else:
    # fail now if secret unreadable
    try:
      secret = open(args.secret).read()
    except IOError, error:
      print error
      print 'No secret found. Have you configured the token?'
      return 1

    if args.daemon:
      print 'Program started, going to background.'
      with daemon.DaemonContext():
        loop(args, secret)

    else:
      print 'Program started, waiting for events.'
      try:
        loop(args, secret)
      except KeyboardInterrupt:
        print '^C'
        return 0

if __name__ == '__main__':
  sys.exit(main())
