#!/usr/bin/env python
"""YubiKey keyboard input: use a YubiKey to send key strokes.


How does it work?

  The YubiKey is configured in OATH-HOTP challenge-response with a random, not
  saved secret. The program picks and saves a random predefined challenge.
  This challenge is used against the token to produce a fixed output string.
  This string is then XOR'd against the input string to create a secret
  saved on the host.
  
  This way, the input string is split in half: half in the token and half
  in the machine. If the token is stolen, an attacker cannot extract the
  half-key without the proper challenge. If the machine is compromised, an
  attacker has one half-key but cannot deduce the input string without the
  other half-key. When you plug the token, the program sends the challenge
  to get back the missing half-key, XOR it with its half-key to get the
  input back. Finally, keystrokes are sent using a virtual keyboard.

  (In reality it is a little more complex: the input string is transformed
  into a key. To allow for large input strings, the key is divided in subkeys
  and there are multiple challenges and half-keys. In addition, a predefined
  challenge-response is used to authenticate the YubiKey before other actions.)


Configuration

  Configure the program with an input string:

    $ python yubinput.py --configure
    Input string: [enter your input string]
    Token and machine configured.


Usage

  Run the program, it stays here and wait:

    $ python yubinput.py
    Program started, waiting for events.

  Insert the same YubiKey. The program uses it to reconstruct the input string
  then sends it back using a virtual keyboard:

    $ python yubinput.py
    Program started, waiting for events.
    2012-03-24T20:18:29+01:00 Sent keyboard input.

  After that, there is a hold delay not to send the input again. Be sure to
  remove the YubiKey within that time or another input will be sent.


Help

  $ python yubinput.py --help
  usage: yubinput.py [-h] [--configure] [--slot SLOT] [--secret SECRET]
                     [--poll POLL] [--hold HOLD] [--daemon] [--xvkbd XVKBD]
                     [--display DISPLAY]
  
  YubiKey keyboard input.
  
  optional arguments:
    -h, --help         show this help message and exit
    --configure        Configure token (default: False)
    --slot SLOT        Configuration slot to use (default: 1)
    --secret SECRET    Location of challenge and half-key file. (default:
                       ~/.yubinput)
    --poll POLL        Polling interval in seconds to check for token (default:
                       1)
    --hold HOLD        Hold delay in seconds before sending another input
                       (default: 10)
    --daemon           Send program to background (default: False)
    --xvkbd XVKBD      Path to xvkbd, X Virtual Keyboard (default:
                       /usr/bin/xvkbd)
    --display DISPLAY  Display to send keys to (default: :0)


Requirements

  xvkbd from http://homepage3.nifty.com/tsato/xvkbd/
  python-argparse
  python-daemon
  python-usb
  python-yubico from https://github.com/Yubico/python-yubico

  Tested with python2.6 and YubiKey 2.2.3.


-- StalkR
"""
import argparse
import daemon
import hashlib
import hmac
import getpass
import os
import random
import subprocess
import struct
import sys
import time
import usb
import yubico

DIGEST_SIZE = hashlib.sha1().digest_size
BLOCK_SIZE = hashlib.sha1().block_size - 1


class Key(object):
  """Class to hold input string, add length and random padding.

  The key consists in:
    - length of input string (4 bytes, little-endian)
    - input string
    - random padding to be multiple of DIGEST_SIZE
  """
  input_string = ''

  def __init__(self, calc='', load=''):
    """Calculate or load a key."""
    if calc:
      self.input_string = calc
    elif load:
      length = struct.unpack('<I', load[:4])[0]
      self.input_string = load[4:][:length]

  def __str__(self):
    assert(len(self.input_string) < 2**32)
    key = struct.pack('<I', len(self.input_string)) + self.input_string
    key += randbytes(-len(key) % DIGEST_SIZE)
    return key


class MachineSecret(object):
  """Class to hold authentication and challenges/half-keys.

  The machine secret consists in:
    - authentication challenge (BLOCK_SIZE bytes)
    - authentication expected response (DIGEST_SIZE bytes)
    - number of subkeys (4 bytes, little-endian)
    - machine challenges (n * BLOCK_SIZE)
    - machine half-keys (n * DIGEST_SIZE)
  """
  auth_challenge = ''
  auth_response = ''
  challenges = []
  half_keys = []

  def __init__(self, calc=(), load=''):
    """Calculate or load machine secret."""
    if calc:
      self.calc(*calc)
    elif load:
      self.load(load)

  def load(self, secret):
    """Load machine secret from saved string."""
    assert(len(secret) > BLOCK_SIZE + DIGEST_SIZE + 4)
    p = 0
    self.auth_challenge = secret[p:][:BLOCK_SIZE]
    p += BLOCK_SIZE
    self.auth_response = secret[p:][:DIGEST_SIZE]
    p += DIGEST_SIZE
    n_subkeys = struct.unpack('<I', secret[p:][:4])[0]
    p += 4

    assert(len(secret[p:]) == n_subkeys * (BLOCK_SIZE + DIGEST_SIZE))
    for _ in range(n_subkeys):
      self.challenges.append(secret[p:][:BLOCK_SIZE])
      p += BLOCK_SIZE
    for _ in range(n_subkeys):
      self.half_keys.append(secret[p:][:DIGEST_SIZE])
      p += DIGEST_SIZE

  def calc(self, input_string, token_secret):
    """Calculate machine secret from input string and token secret.

    Since input string can be long, prepend with length and pad it. It becomes
    the key, divide it in subkeys and for each:
      - generate a random machine challenge
      - get the output from OATH-HOTP with this challenge: token half-key
      - xor it with the subkey: machine half-key

    Also, prepare a precomputed challenge-response to do basic authentication of
    the token.
    """
    # prepare key with length and random padding
    key = str(Key(input_string))

    self.auth_challenge = randbytes(BLOCK_SIZE)
    self.auth_response = hotp(token_secret, self.auth_challenge)

    # divide key in subkeys to compute challenges and half-keys
    for i in range(len(key) / DIGEST_SIZE):
      subkey = key[i*DIGEST_SIZE:][:DIGEST_SIZE]
      machine_challenge = randbytes(BLOCK_SIZE)

      # compute token half-key as token would return it
      token_half_key = hotp(token_secret, machine_challenge)
      # deduce machine half-key
      machine_half_key = xor(subkey, token_half_key)

      self.challenges.append(machine_challenge)
      self.half_keys.append(machine_half_key)

  def derive(self, token, slot=1):
    """Derive input string from machine secret (inverse of calc)."""
    subkeys = []
    # rebuild every subkey from machine and token half-keys
    for i in range(self.n_subkeys):
      token_half_key = challenge_response(token, self.challenges[i], slot)
      subkeys.append(xor(self.half_keys[i], token_half_key))

    return Key(load=''.join(subkeys)).input_string

  def __str__(self):
    return (self.auth_challenge +
            self.auth_response +
            struct.pack('<I', self.n_subkeys) +
            ''.join(self.challenges) +
            ''.join(self.half_keys))

  @property
  def n_subkeys(self):
    """Accessor for the number of subkeys, with safe checks."""
    n_subkeys = len(self.challenges)
    assert(n_subkeys == len(self.half_keys))
    assert(n_subkeys < 2**32)
    return n_subkeys


def hotp(secret, counter, hashfunc=hashlib.sha1):
  """Generic HOTP algorithm, secret/counter are strings."""
  return hmac.new(secret, counter, hashfunc).digest()

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

def xor(a, b):
  """Character by character xor of string a and b of same length."""
  assert(len(a) == len(b))
  return "".join(chr(ord(a[i]) ^ ord(b[i])) for i in range(len(a)))

def send_input(args, string):
  """Send keyboard input, here using xvkbd but can be extended.

  Other programs to send input on Linux:
    - xte "key x" "key y" (package xautomation)
    - xdotool key x+y (package xdotool)
  For Windows, a Python library: http://www.rutherfurd.net/python/sendkeys/
  """
  proc = subprocess.Popen([args.xvkbd,
                          "-display", args.display,
                          "-text", string],
                          stderr=subprocess.PIPE)
  status = proc.wait()
  if status != 0:
    log('Warning: xvkbd exited with non-zero %i' % status)

def are_chars_all_in(string, charset):
  """Checks if all characters in string are in charset."""
  for c in string:
    if c not in charset:
      return False
  return True

def is_invalid_input(string):
  """Checks if string is in string.printable without \t\n\r\x0b\x0c."""
  charset = ('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
             '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ')
  return not are_chars_all_in(string, charset)

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
    print 'Configuration failed: %s' % str(error)
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
  """Compute and configure half-keys for machine and token."""
  input_string = getpass.getpass('Input string: ')
  if is_invalid_input(input_string):
    print 'Invalid input string (bad chars or too long).'
    return 1

  token_secret = randbytes(DIGEST_SIZE)
  if not configure_token(token_secret, args.slot):
    return 1

  machine_secret = MachineSecret(calc=(input_string, token_secret))
  if not save_secret(str(machine_secret), args.secret):
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

def loop(args, machine_secret):
  """Wait for correct token to be inserted and send input."""
  while True:
    # wait for tokens
    while True:
      tokens = find_tokens()
      if tokens:
        break
      time.sleep(args.poll)

    # try to authenticate all available tokens, send input if success
    for token in tokens:
      obtained = challenge_response(token, machine_secret.auth_challenge,
                                    args.slot)
      expected = machine_secret.auth_response
      if obtained == expected:
        log('Sent input.')
        send_input(args, machine_secret.derive(token, args.slot))
        time.sleep(args.hold)

    time.sleep(args.poll)

def parse_args():
  """Parse the command line arguments."""
  parser = argparse.ArgumentParser(
      description = 'YubiKey keyboard input.',
      add_help = True,
      formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--configure', action='store_true', default=False,
                      help='Configure token')
  parser.add_argument('--slot', type=int, default=1,
                      help='Configuration slot to use')
  parser.add_argument('--secret', type=str, default='~/.yubinput',
                      help='Location of challenge and half-key file.')
  parser.add_argument('--poll', type=float, default=1,
                      help='Polling interval in seconds to check for token')
  parser.add_argument('--hold', type=float, default=10,
                      help='Hold delay in seconds before sending another input')
  parser.add_argument('--daemon', action='store_true', default=False,
                      help='Send program to background')
  parser.add_argument('--xvkbd', type=str, default='/usr/bin/xvkbd',
                      help='Path to xvkbd, X Virtual Keyboard')
  parser.add_argument('--display', type=str, default=':0',
                      help='Display to send keys to')

  args = parser.parse_args()
  args.secret = os.path.expanduser(args.secret)
  return args

def main():
  """Entry point."""
  args = parse_args()

  if args.configure:
    return configure(args)

  else:
    # fail now if (machine) secret unreadable or invalid
    try:
      secret = open(args.secret).read()
    except IOError, error:
      print error
      print 'No secret found. Have you configured the token?'
      return 1

    try:
      machine_secret = MachineSecret(load=secret)
    except AssertionError:
      print 'Secret looks corrupted, please reconfigure.'
      return 1

    if args.daemon:
      print 'Program started, going to background.'
      with daemon.DaemonContext():
        loop(args, machine_secret)

    else:
      print 'Program started, waiting for events.'
      try:
        loop(args, machine_secret)
      except KeyboardInterrupt:
        print '^C'
        return 0

if __name__ == '__main__':
  sys.exit(main())
