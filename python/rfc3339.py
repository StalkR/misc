#!/usr/bin/python
"""Date in RFC3339 format."""

__author__ = 'StalkR'

import time


def date(secs=None):
  """Print date in RFC3339 format with local time.

  Args:
    secs: Seconds since the epoch, if None the current time is used.

  Returns:
    A string with the date in RFC3339 format with local time.
  """
  s_date = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(secs))
  s_tz = stroffset(tzoffset(secs))
  return s_date + s_tz


def tzoffset(secs=None):
  """Calculate time zone offset taking DST into account.

  Args:
    secs: Seconds since the epoch, if None the current time is used.

  Returns:
    A signed integer representing the offset in seconds.
  """
  secs_utc = int(time.strftime('%s', time.gmtime(secs)))
  local = time.localtime(secs)
  secs_local = int(time.strftime('%s', local)) + local.tm_isdst*3600
  return secs_local - secs_utc


def stroffset(offset):
  """Represent a timezone offset into a string.

  Args:
    offset: A signed integer representing the offset in seconds.

  Returns:
    A string with the offset, with sign (+/-) and hours:minutes (e.g. +00:00).
  """
  sign = '+' if offset >= 0 else '-'
  hours = abs(offset)/3600
  minutes = abs(offset)/60 % 60
  return '%s%02i:%02i' % (sign, hours, minutes)

