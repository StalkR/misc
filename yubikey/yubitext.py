#!/usr/bin/env python
"""YubiText: use a YubiKey to send text using a virtual keyboard.


How does it work?

  You configure the program with a text and a YubiKey on a specific machine.
  Whenever you plug the same YubiKey on this machine, the program types the
  text you configured using a virtual keyboard.


Details

  The YubiKey is configured in HMAC-SHA1 challenge-response with a random, not
  saved secret. The program picks and saves a random challenge that is used
  against the token to produce the token half-key. The token half-key is XOR'd
  against the text to create the machine half-key, saved on the machine.
  When the YubiKey is plugged, the text is retrieved with:
    text = YubiKey_response(machine_challenge) XOR machine_half-key
            \------- token_half-key --------/

  In practice, the text is transformed into a key. To allow for large text, the
  key is divided in subkeys and there are multiple challenges and machine
  secrets. In addition, a predefined challenge-response is used to
  authenticate the YubiKey before other actions.


Configuration

  Configure the program with some text:

    $ python yubitext.py --configure
    Text (not echoed): [xxxxxxx]
    Token programmed.
    Machine configured.


Usage

  Run the program, it stays here and waits for udev USB events:

    $ python yubitext.py
    Program started, waiting for events.

  Insert the same YubiKey. After authentication, the program uses it to
  reconstruct the text and sends it using a virtual keyboard:

    $ python yubitext.py
    Program started, waiting for events.
    [date...] YubiKey plugged: authenticate all plugged YubiKeys.
    [date...] * YubiKey 2.2.3 serial 1234567 authenticated, sending text.


Help

  $ python yubitext.py --help
  usage: yubitext.py [-h] [--configure] [--program yes|no] [--slot N]
                     [--secret FILE] [--daemon] [--xvkbd PATH] [--display :N]

  YubiKey keyboard input.

  optional arguments:
    -h, --help        show this help message and exit
    --configure       Configure input text (default: False)
    --program yes|no  Program token (default: yes)
    --slot N          Configuration slot to use (default: 1)
    --secret FILE     Location of machine secret file. (default: ~/.yubitext)
    --daemon          Send program to background and logs to syslog. (default:
                      False)
    --xvkbd PATH      Path to xvkbd, X Virtual Keyboard (default:
                      /usr/bin/xvkbd)
    --display :N      Display to send keys to (default: :0)


Requirements

  xvkbd from http://homepage3.nifty.com/tsato/xvkbd/
  python-argparse
  python-daemon
  python-gudev
  python-usb
  python-yubico from https://github.com/Yubico/python-yubico

  Tested with python2.6 and YubiKey 2.2.3.
"""
import argparse
import daemon
import hashlib
import getpass
import gobject
import gudev
import os
import random
import subprocess
import string
import struct
import sys
import syslog
import time
import usb
import yubico

__author__ = 'stalkr@stalkr.net (StalkR)'

TEXT_MAX = 2**14  # 16384
DIGEST_SIZE = hashlib.sha1().digest_size
CHALLENGE_SIZE = hashlib.sha1().block_size - 1


class Key(object):
  """Class for key: text with length and random padding.

  The string representation is:
    - length of text (2 bytes, little-endian)
    - text
    - random padding to be multiple of DIGEST_SIZE

  Attributes:
    text: A string for the text the key contains.
  """
  text = ''

  def __init__(self, text=None):
    """Prepare a new key object from text."""
    self.text = text

  def __str__(self):
    """Build key string from object.

    Raises:
      AssertError: The text is too big.
    """
    assert(len(self.text) < 2**16)
    key = struct.pack('<H', len(self.text)) + self.text
    key += randbytes(-len(key) % DIGEST_SIZE)
    return key

  def load(self, load):
    """Restore key object from string.

    Args:
      load: The string representation of a Key produced by str(Key).

    Raises:
      AssertError: The string is incorrect, does not represent a Key.
    """
    assert(len(load) >= 2)
    length = struct.unpack('<H', load[:2])[0]
    self.text = load[2:][:length]
    assert(len(self.text) == length)


class MachineSecret(object):
  """Class to hold machine secret: authentication, challenges and half-keys.

  The string representation is:
    - authentication challenge (CHALLENGE_SIZE bytes)
    - authentication expected response (DIGEST_SIZE bytes)
    - number of subkeys (2 bytes, little-endian)
    - machine challenges (n * CHALLENGE_SIZE)
    - machine half-keys (n * DIGEST_SIZE)

  Attributes:
    auth_challenge: String of CHALLENGE_SIZE sent to the token for auth.
    auth_response: String of DIGEST_SIZE to expect from the token.
    challenges: List of strings of CHALLENGE_SIZE sent to the token.
    half_keys: List of strings of DIGEST_SIZE xor'd with the token responses
        to the challenges to produce the key.
  """
  auth_challenge = ''
  auth_response = ''
  challenges = []
  half_keys = []

  def __str__(self):
    """Build machine secret string from object."""
    return (self.auth_challenge +
            self.auth_response +
            struct.pack('<H', self.n_subkeys) +
            ''.join(self.challenges) +
            ''.join(self.half_keys))

  def load(self, secret):
    """Restore machine secret object from string.

    Raises:
      AssertError: The string is incorrect, does not represent a MachineSecret.
    """
    assert(len(secret) > CHALLENGE_SIZE + DIGEST_SIZE + 2)
    p = 0
    self.auth_challenge = secret[p:][:CHALLENGE_SIZE]
    p += CHALLENGE_SIZE
    self.auth_response = secret[p:][:DIGEST_SIZE]
    p += DIGEST_SIZE
    n_subkeys = struct.unpack('<H', secret[p:][:2])[0]
    p += 2

    assert(len(secret[p:]) == n_subkeys * (CHALLENGE_SIZE + DIGEST_SIZE))
    for _ in range(n_subkeys):
      self.challenges.append(secret[p:][:CHALLENGE_SIZE])
      p += CHALLENGE_SIZE
    for _ in range(n_subkeys):
      self.half_keys.append(secret[p:][:DIGEST_SIZE])
      p += DIGEST_SIZE

  def build(self, text, token):
    """Build a new machine secret from text and token.

    Generate a precomputed challenge-response to do basic authentication.
    Create key from text, divide it in subkeys and for each:
      - generate a random machine challenge
      - ask the token the answer to that
      - xor it with the subkey: machine half-key
    When it returns, the object is updated and ready to be exported.

    Args:
      text: A string of the text to store.
      token: A Token object.
    """
    key = str(Key(text))

    self.auth_challenge = randbytes(CHALLENGE_SIZE)
    self.auth_response = token.challenge(self.auth_challenge)

    for i in range(len(key) / DIGEST_SIZE):
      subkey = key[i*DIGEST_SIZE:][:DIGEST_SIZE]
      challenge = randbytes(CHALLENGE_SIZE)

      token_half_key = token.challenge(challenge)
      machine_half_key = xor(subkey, token_half_key)

      self.challenges.append(challenge)
      self.half_keys.append(machine_half_key)

  def extract(self, token):
    """Authentify then extract text from machine secret and token.

    Args:
      token: A Token object.

    Returns:
      A string of the text that was stored at build.
    """
    if token.challenge(self.auth_challenge) != self.auth_response:
      return None

    subkeys = []
    for i in range(self.n_subkeys):
      token_half_key = token.challenge(self.challenges[i])
      subkeys.append(xor(self.half_keys[i], token_half_key))

    key = Key()
    key.load(''.join(subkeys))
    return key.text

  @property
  def n_subkeys(self):
    """Accessor for the number of subkeys.

    Raises:
      AssertError: The object is inconsistent or there are too many subkeys.
    """
    n_subkeys = len(self.challenges)
    assert(n_subkeys == len(self.half_keys))
    assert(n_subkeys < 2**16)
    return n_subkeys


class Token(object):
  """Abstract class of a token from the point of view of MachineSecret."""

  def challenge(self, challenge):
    """Send challenge to token and receive response.

    Args:
      challenge: String of size CHALLENGE_SIZE to send to token.

    Returns:
      A string of DIGEST_SIZE that is the token response to the challenge.
    """
    pass


class YubiKeyError(Exception):
  """Base exception class for errors related to YubiKey."""
  pass


class YubiKey(Token):
  """Class to abstract YubiKeys and provide safe methods.

  Attributes:
    yubikey: A yubico.yubikey.YubiKey object or None.
    slot: An integer for the configuration slot to use.
  """

  @staticmethod
  def find(slot=1):
    """Iterate over all available YubiKeys using skip parameter."""
    for skip in range(256):
      try:
        yield YubiKey(yubico.find_yubikey(skip=skip), slot)
      except yubico.yubikey.YubiKeyError, error:
        if error.reason == 'No YubiKey found':
          break  # no more YubiKeys
      except usb.USBError:
        pass

  def __init__(self, yubikey=None, slot=1):
    """Receive a yubico.yubikey object and configuration slot."""
    self.yubikey = yubikey
    self.slot = slot

  def __str__(self):
    """Display information about YubiKey: version, serial."""
    version = serial = 'n/a'

    if self.yubikey is not None:
      try:
        version = self.yubikey.version()
      except yubico.yubikey.YubiKeyError:
        pass
      except usb.USBError:
        pass

      try:
        serial = '%i' % self.yubikey.serial()
      except yubico.yubikey.YubiKeyError:
        pass
      except usb.USBError:
        pass

    return 'YubiKey %s serial %s' % (version, serial)

  def configure(self, secret):
    """Configures YubiKey in challenge-response OATH-HOTP with secret.

    Args:
      secret: String of size DIGEST_SIZE to store in YubiKey for HMAC.

    Raises:
      YubiKeyError: An error occured when communicating with the YubiKey.
    """
    try:
      cfg = self.yubikey.init_config()
      cfg.mode_challenge_response(secret, type='HMAC', variable=True,
                                  require_button=False)
      cfg.extended_flag('SERIAL_API_VISIBLE', True)
      self.yubikey.write_config(cfg, slot=self.slot)
    except yubico.yubikey.YubiKeyError, error:
      raise YubiKeyError(error.reason)
    except yubico.yubikey_usb_hid.YubiKeyUSBHIDError, error:
      raise YubiKeyError(str(error))

  def challenge(self, challenge):
    """Send challenge to YubiKey and receive response.

    Args:
      challenge: String of size CHALLENGE_SIZE to send to YubiKey.

    Returns:
      A string of DIGEST_SIZE that is YubiKey HMAC of the challenge.

    Raises:
      YubiKeyError: An error occured when communicating with the YubiKey.
    """
    try:
      return self.yubikey.challenge_response(challenge, slot=self.slot)
    except yubico.yubikey.YubiKeyError, error:
      raise YubiKeyError(error.reason)
    except usb.USBError, error:
      raise YubiKeyError(str(error))


def randbytes(size):
  """Return a string of random bytes."""
  return ''.join(chr(random.randint(0, 255)) for _ in range(size))

def log(args, message):
  """Log message with date prepended."""
  if args.daemon:
    syslog.syslog(message)
  else:
    # date in RFC3339 format
    tmz = time.strftime('%z')
    date = time.strftime('%Y-%m-%dT%H:%M:%S') + tmz[:3] + ':' + tmz[3:]
    print '%s %s' % (date, message)

def xor(a, b):
  """Character by character xor of string a and b of same length."""
  assert(len(a) == len(b))
  return ''.join(chr(ord(a[i]) ^ ord(b[i])) for i in range(len(a)))

def send_input(args, text):
  """Send keyboard input, here using xvkbd but can be extended.

  Other programs to send input on Linux:
    - xte "key x" "key y" (package xautomation)
    - xdotool key x+y (package xdotool)
  For Windows, a Python library: http://www.rutherfurd.net/python/sendkeys/
  """
  proc = subprocess.Popen([args.xvkbd,
                          "-display", args.display,
                          "-text", text],
                          stderr=subprocess.PIPE)
  status = proc.wait()
  if not args.daemon and status != 0:
    log(args, 'Warning: send input exited with non-zero %i' % status)

def yubikey_inserted(args, machine_secret):
  """Authenticate plugged YubiKeys, send input if successful."""
  if not args.daemon:
    log(args, 'YubiKey plugged: authenticate all plugged YubiKeys.')

  for yubikey in YubiKey.find(args.slot):
    try:
      text = machine_secret.extract(yubikey)
    except YubiKeyError:
      if not args.daemon:
        log(args, '* %s, not the YubiKey we are looking for.' % yubikey)
      continue

    if text is None:
      log(args, '* %s, authentication failed.' % yubikey)
    else:
      log(args, '* %s, authenticated, sending text.' % yubikey)
      send_input(args, text)
      return

def loop(args, machine_secret):
  """Wait for YubiKeys to be inserted, udev triggers."""

  def usb_event(client, event, device):
    """GUDev handler when an USB event triggers."""
    if (device.get_action() == 'add' and
        device.get_property('ID_VENDOR') == 'Yubico' and
        device.get_property('ID_MODEL') == 'Yubico_Yubikey_II'):
      yubikey_inserted(args, machine_secret)

  client = gudev.Client(['usb'])
  client.connect('uevent', usb_event)
  gobject.MainLoop().run()

def configure(args):
  """Get text, program token, build machine secret and save it."""
  text = getpass.getpass('Text (not echoed): ')
  charset = string.printable.strip() + ' '  # no whitespaces except space
  if not all(c in charset for c in text) or len(text) > TEXT_MAX: 
    print 'Invalid text, bad chars or too long.'
    return 1

  yubikeys = [_ for _ in YubiKey.find(args.slot)]
  if not len(yubikeys) or len(yubikeys) > 1:
    print 'Please plug a YubiKey and only one.'
    return 1

  yubikey = yubikeys.pop()
  if args.program:
    try:
      yubikey.configure(randbytes(DIGEST_SIZE))
    except YubiKeyError, error:
      print 'Token programming error:', error
      return 1
    print 'Token programmed.'

  machine_secret = MachineSecret()
  try:
    machine_secret.build(text, yubikey)
  except YubiKeyError, error:
    print 'Configuration error:', error
    return 1

  try:
    open(args.secret, 'w').write(str(machine_secret))
  except IOError, error:
    print error
    print 'Error saving machine secret'
    return 1
  try:  # attempt user only permission
    os.chmod(args.secret, 0600)
  except OSError:
    pass

  print 'Machine configured.'
  return 0

def parse_args():
  """Parse the command line arguments."""
  parser = argparse.ArgumentParser(
      description = 'YubiKey keyboard input.',
      add_help = True,
      formatter_class = argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--configure', action='store_true', default=False,
                      help='Configure input text')
  parser.add_argument('--program', metavar='yes|no', type=str, default='yes',
                      choices=('yes','no'), help='Program token')
  parser.add_argument('--slot', metavar='N', type=int, default=1,
                      help='Configuration slot to use')
  parser.add_argument('--secret', metavar='FILE', type=str,
                      default='~/.yubitext',
                      help='Location of machine secret file.')
  parser.add_argument('--daemon', action='store_true', default=False,
                      help='Send program to background and logs to syslog.')
  parser.add_argument('--xvkbd', metavar='PATH', type=str,
                      default='/usr/bin/xvkbd',
                      help='Path to xvkbd, X Virtual Keyboard')
  parser.add_argument('--display', metavar=':N', type=str, default=':0',
                      help='Display to send keys to')

  args = parser.parse_args()
  args.secret = os.path.expanduser(args.secret)
  args.xvkbd = os.path.expanduser(args.xvkbd)
  args.program = args.program == 'yes'
  return args

def main():
  """Entry point."""
  args = parse_args()
  if args.configure:
    return configure(args)

  try:
    secret = open(args.secret).read()
  except IOError, error:
    print error
    print 'No secret found. Is it configured?'
    return 1
  machine_secret = MachineSecret()
  try:
    machine_secret.load(secret)
  except AssertionError:
    print 'Secret looks corrupted, please reconfigure.'
    return 1

  if args.daemon:
    print 'Program started, going to background.'
    with daemon.DaemonContext():
      syslog.openlog('yubitext', syslog.LOG_PID, syslog.LOG_AUTH)
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
