"""Tests for Burp base64 editor library.

These unit tests allow us to test the extension outside of burp and iterate
faster compared to reloading the extension in Burp, slow with Jython.
"""

import b64
import unittest


class TestRequest(unittest.TestCase):

  def testDisabled(self):
    req = b64.Request.Parse('POST / HTTP/1.1\r\n\r\n<not>')
    self.assertFalse(req.Enabled())

  def testDecodeEncode(self):
    req = b64.Request.Parse('POST / HTTP/1.1\r\n\r\naGVsbG8=')
    self.assertTrue(req.Enabled())
    self.assertEqual('hello', req.Text())
    req.Load('bye bye')
    self.assertEqual('POST / HTTP/1.1\r\n\r\nYnllIGJ5ZQ==', req.String())


class TestResponse(unittest.TestCase):

  def testDisabled(self):
    resp = b64.Response.Parse('HTTP/1.1 200 OK\r\n\r\n<not>')
    self.assertFalse(resp.Enabled())

  def testDecode(self):
    resp = b64.Response.Parse('HTTP/1.1 200 OK\r\n\r\nd29ya3M=')
    self.assertTrue(resp.Enabled())
    self.assertEqual('works', resp.Text())


if __name__ == '__main__':
    unittest.main()
