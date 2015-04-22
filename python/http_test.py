#!/usr/bin/python
"""Tests for http library."""

import http
import unittest


class TestRequest(unittest.TestCase):

  def testSimple(self):
    m = 'GET /?x HTTP/1.1\r\nHost: y\r\n\r\nbody'
    r = http.Request(m)
    self.assertEqual('GET', r.Method)
    self.assertEqual('/', r.Path)
    self.assertEqual('x', r.Query)
    self.assertEqual('HTTP/1.1', r.Version)
    self.assertEqual('y', r.Headers.Get('host'))
    self.assertEqual('body', r.Body)
    self.assertEqual(m, r.String())


class TestResponse(unittest.TestCase):

  def testSimple(self):
    m = 'HTTP/1.1 200 It works\r\nServer: x\r\n\r\nbody'
    r = http.Response(m)
    self.assertEqual('HTTP/1.1', r.Version)
    self.assertEqual(200, r.Status)
    self.assertEqual('It works', r.Message)
    self.assertEqual('x', r.Headers.Get('server'))
    self.assertEqual('body', r.Body)
    self.assertEqual(m, r.String())


class TestHeaders(unittest.TestCase):
  
  def testSimple(self):
    s = 'A: b\r\nC: d'
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


if __name__ == '__main__':
    unittest.main()
