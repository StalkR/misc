#!/usr/bin/python
"""Library to manipulate HTTP messages."""

import urllib


class Error(Exception):
  """Base exception class for library errors."""


class Request(object):
  """Request represents an HTTP request."""

  def __init__(self, content=''):
    if not content:
      return
    f, h, b = parse(content)
    w = f.split(' ')
    if len(w) != 3:
      raise Error('invalid request')
    self.Method = w[0]
    self.Version = w[2]
    q = w[1].split('?')
    self.Path = q[0]
    self.Query = q[1] if len(q) > 1 else ''
    self.Headers = Headers(h)
    self.Body = b

  def String(self):
    path = self.Path
    return '%s %s %s\r\n%s\r\n\r\n%s' % (
          self.Method,
          '%s?%s' % (path, self.Query) if self.Query else path,
          self.Version,
          self.Headers.String(),
          self.Body
      )


class Response(object):
  """Response represents an HTTP response."""

  def __init__(self, content=''):
    if not content:
      return
    f, h, b = parse(content)
    w = f.split(' ', 2)
    if len(w) < 3:
      raise Error('invalid response')
    self.Version = w[0]
    self.Status = int(w[1])
    self.Message = w[2]
    self.Headers = Headers(h)
    self.Body = b

  def String(self):
    return '%s %i %s\r\n%s\r\n\r\n%s' % (
          self.Version,
          self.Status,
          self.Message,
          self.Headers.String(),
          self.Body
      )


class Headers(object):
  """Headers represents headers of an HTTP message."""

  def __init__(self, headers):
    self.h = []
    for line in headers.split('\r\n'):
      w = line.split(':', 1)
      if len(w) == 1:
        self.Add(w[0], '')
      else:
        self.Add(w[0], w[1].lstrip())

  def Add(self, name, value):
    self.h.append((name, value))

  def Del(self, name):
    for key, value in self.h:
      if key.lower() == name.lower():
        self.h.remove((key, value))

  def Get(self, name):
    for key, value in self.h:
      if key.lower() == name.lower():
        return value

  def Set(self, name, value):
    self.Del(name)
    self.Add(name, value)

  def String(self):
    return '\r\n'.join('%s: %s' % (key, value) for key, value in self.h)


class Values(object):
  """Values represents values in a query parameter."""

  def __init__(self, q=''):
    self.v = []
    p = q.find('#')
    if p != -1:
      q = q[:p]
    for a in q.split('&'):
      w = a.split('=', 1)
      if len(w) == 1:
        self.Add(w[0], '')
      else:
        self.Add(queryUnescape(w[0]), queryUnescape(w[1]))

  def Add(self, name, value):
    self.v.append((name, value))

  def Del(self, name):
    for key, value in self.v:
      if key == name:
        self.v.remove((key, value))

  def Get(self, name):
    for key, value in self.v:
      if key == name:
        return value

  def Set(self, name, value):
    self.Del(name)
    self.Add(name, value)

  def Encode(self):
    v = []
    for key, value in self.v:
      if value:
        v.append('%s=%s' % (queryEscape(key), queryEscape(value)))
      else:
        v.append(queryEscape(key))
    return '&'.join(v)


def parse(m):
  """parse parses an HTTP message into 3 parts: first line, headers, body."""
  p = m.find('\r\n')
  if p == -1:
    raise Error('invalid message')
  first = m[:p]
  q = m.find('\r\n\r\n')
  headers = m[p+2:q]
  body = m[q+4:]
  return first, headers, body


def queryEscape(s):
  return urllib.quote_plus(s)


def queryUnescape(s):
  return urllib.unquote_plus(s)
