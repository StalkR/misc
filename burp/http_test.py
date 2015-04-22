"""Tests for http library."""

import http
import unittest


class TestRequest(unittest.TestCase):

  def testSimple(self):
    s = 'POST /?x HTTP/1.1\r\nHost: y\r\n\r\nbody'
    r = http.Request.Parse(s)
    self.assertEqual('POST', r.Method)
    self.assertEqual('/', r.Path)
    self.assertEqual('x', r.Query)
    self.assertEqual('HTTP/1.1', r.Version)
    self.assertEqual('y', r.Headers.Get('host'))
    self.assertEqual('body', r.Body)
    self.assertEqual(s, r.String())

  def testNoHeaders(self):
    s = 'POST / HTTP/1.0\r\n\r\nbody'
    req = http.Request.Parse(s)
    self.assertEqual(s, req.String())



class TestResponse(unittest.TestCase):

  def testSimple(self):
    s = 'HTTP/1.1 200 It works\r\nServer: x\r\n\r\nbody'
    r = http.Response.Parse(s)
    self.assertEqual('HTTP/1.1', r.Version)
    self.assertEqual(200, r.Status)
    self.assertEqual('It works', r.Message)
    self.assertEqual('x', r.Headers.Get('server'))
    self.assertEqual('body', r.Body)
    self.assertEqual(s, r.String())

  def testNoHeaders(self):
    s = 'HTTP/1.1 200 OK\r\n\r\nbody'
    req = http.Request.Parse(s)
    self.assertEqual(s, req.String())


class TestHeaders(unittest.TestCase):
  
  def testSimple(self):
    s = 'A: b\r\nC: d\r\n'
    h = http.Headers(s)
    self.assertEqual('b', h.Get('a'))
    self.assertEqual('d', h.Get('c'))
    self.assertEqual(s, h.String())
    h.Add('a', 'x')
    self.assertEqual('b', h.Get('a'))
    h.Set('a', 'x')
    self.assertEqual('x', h.Get('a'))
    h.Del('a')
    self.assertEqual(None, h.Get('a'))

  def testEmpty(self):
    self.assertEqual(http.Headers().h, [])
    self.assertEqual(http.Headers('\r\n\r\n').h, [])
    self.assertEqual(http.Headers(': xx\r\n').h, [])


class TestValues(unittest.TestCase):
  
  def testSimple(self):
    v = http.Values('a=b&c=d')
    self.assertEqual('b', v.Get('a'))
    self.assertEqual('d', v.Get('c'))
    v.Add('a', 'x')
    self.assertEqual('b', v.Get('a'))
    v.Set('a', 'x')
    self.assertEqual('x', v.Get('a'))
    v.Del('a')
    self.assertEqual(None, v.Get('a'))

  def testEmpty(self):
    self.assertEqual(http.Values().v, [])
    self.assertEqual(http.Values('&&&').v, [])
    self.assertEqual(http.Values('&=1').v, [])


if __name__ == '__main__':
    unittest.main()
