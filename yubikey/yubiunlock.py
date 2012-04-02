#!/usr/bin/env python
"""YubiKey screen unlocker: unlock your screen using a YubiKey.


Configuration

  Configure a YubiKey in OATH-HOTP challenge-response with a secret shared with
  the host:

    $ python yubiunlock.py --configure
    Token and machine configured.


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
  usage: yubiunlock.py [-h] [--configure] [--slot SLOT] [--secret SECRET]
                       [--poll POLL] [--daemon] [--screensaver SCREENSAVER]
  
  YubiKey screen unlocker.
  
  optional arguments:
    -h, --help            show this help message and exit
    --configure           Configure token (default: False)
    --slot SLOT           Configuration slot to use (default: 1)
    --secret SECRET       Location of shared secret file. (default:
                          ~/.yubiunlock)
    --poll POLL           Polling interval in seconds to check for token
                          (default: 1)
    --daemon              Send program to background (default: False)
    --screensaver SCREENSAVER
                          Name of screensaver process to kill (default: gnome-
                          screensaver)


Requirements

  python-argparse
  python-daemon
  python-psutil
  python-usb
  python-yubico from https://github.com/Yubico/python-yubico

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

DIGEST_SIZE = hashlib.sha1().digest_size
BLOCK_SIZE = hashlib.sha1().block_size - 1

def hotp(secret, counter, algo=hashlib.sha1):
  """Generic HOTP algorithm, secret/counter are strings."""
  return hmac.new(secret, counter, algo).digest()

def randbytes(size):
  """Return a string of random bytes."""
  return ''.join(chr(random.randint(0, 255)) for _ in range(size))

def date():
  """Date in RFC3339 format."""
  tmz = time.strftime('%z')
  return time.strftime('%Y-%m-%dT%H:%M:%S') + tmz[:3] + ':' + tmz[3:]

def log(msg):
  """Log message with date prepended."""
  print '%s %s' % (date(), msg)

def configure_token(secret, slot=1):
  """Configures Token in OATH-HOTP challenge-response with secret."""
  try:
    token = yubico.find_yubikey()
    cfg = token.init_config()
    cfg.mode_challenge_response(secret, type='HMAC', variable=True,
                                require_button=False)
    cfg.extended_flag('SERIAL_API_VISIBLE', True)
    token.write_config(cfg, slot=slot)

  except yubico.yubikey.YubiKeyError, error:
    print 'Configuration failed: %s' % str(error)
    return False

  except yubico.yubikey_usb_hid.YubiKeyUSBHIDError, error:
    print 'Unable to create secret file: %s' % str(error)
    return False

  return True

def save_secret(secret, filename):
  """Save secret to file with user permission only if possible."""
  try:
    open(filename, 'w').write(secret)
  except IOError:
    return False

  try:
    os.chmod(filename, 0600)
  except OSError:
    pass

  return True

def configure(args):
  """Configure token and save secret in file."""
  secret = randbytes(DIGEST_SIZE)
  if not configure_token(secret, args.slot):
    return 1

  if not save_secret(secret, args.secret):
    return 1

  print 'Token and machine configured.'
  return 0

def find_tokens():
  """Iterate over all available tokens."""
  for skip in range(256):
    try:
      yield yubico.find_yubikey(skip=skip)
    except yubico.yubikey.YubiKeyError:
      pass
    except usb.USBError:
      pass

def challenge_response(token, challenge, slot=1):
  """Send challenge to token and receive response."""
  try:
    return token.challenge_response(challenge, slot=slot)
  except yubico.yubikey.YubiKeyError:
    pass
  except usb.USBError:
    pass
  return ''

def authentify(token, secret, slot=1):
  """Authentify token with challenge-response."""
  challenge = randbytes(BLOCK_SIZE)
  expected = hotp(secret, challenge)
  return challenge_response(token, challenge, slot) == expected

def screensaver(name):
  """Return screensaver process if found or None."""
  for process in psutil.process_iter():
    if process.name == name:
      return process
  return None

def loop(args, secret):
  """Unlock screen when locked and token present."""
  proc = None
  while True:
    # wait for screensaver
    while not proc:
      proc = screensaver(args.screensaver)
      if proc:
        break
      time.sleep(args.poll)

    # wait for token
    while True:
      # we lost screensaver, go back find it
      if not proc.is_running():
        proc = None
        break

      # try to authenticate all available tokens
      for token in find_tokens():
        if authentify(token, secret, args.slot):
          log('Unlocked screen.')
          proc.kill()

      time.sleep(args.poll)

def parse_args():
  """Parse the command line arguments."""
  parser = argparse.ArgumentParser(
      description = 'YubiKey screen unlocker.',
      add_help = True,
      formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--configure', action='store_true', default=False,
                      help='Configure token')
  parser.add_argument('--slot', type=int, default=1,
                      help='Configuration slot to use')
  parser.add_argument('--secret', type=str, default='~/.yubiunlock',
                      help='Location of shared secret file.')
  parser.add_argument('--poll', type=float, default=1,
                      help='Polling interval in seconds to check for token')
  parser.add_argument('--daemon', action='store_true', default=False,
                      help='Send program to background')
  parser.add_argument('--screensaver', type=str, default='gnome-screensaver',
                      help='Name of screensaver process to kill')

  args = parser.parse_args()
  args.secret = os.path.expanduser(args.secret)
  return args

def main():
  """Entry point."""
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
