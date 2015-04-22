"""Tests for user agent library.

This demonstrates the power of unit tests to test your extension with real
traffic examples: it saves a lot of time compared to developing directly in
burp and reloading the extension every time, which takes time with Jython.
"""

import useragent as ua
import unittest


class TestRequest(unittest.TestCase):

  def testRoundTrip(self):
    req = ua.Request.Parse('GET / HTTP/1.1\r\nUser-Agent: python\r\n\r\n')
    self.assertTrue(req.Enabled())
    self.assertEqual('python', req.Text())
    req.Load('x')
    self.assertEqual('GET / HTTP/1.1\r\nUser-Agent: x\r\n\r\n', req.String())


class TestResponse(unittest.TestCase):

  def testResponse(self):
    resp = ua.Response.Parse('HTTP/1.1 200 OK\r\n\r\nok')
    self.assertFalse(resp.Enabled())
    self.assertEqual('', resp.Text())


if __name__ == '__main__':
    unittest.main()
