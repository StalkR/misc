"""Tests for Burp zlib editor library.

These unit tests allow us to test the extension outside of burp and iterate
faster compared to reloading the extension in Burp, slow with Jython."""

import zlibedit
import unittest


class TestRequest(unittest.TestCase):

  def testDisabled(self):
    req = zlibedit.Request.Parse('POST / HTTP/1.1\r\n\r\n<not>')
    self.assertFalse(req.Enabled())

  def testDecodeEncode(self):
    req = zlibedit.Request.Parse('POST / HTTP/1.1\r\n\r\n' + 
        'x\x9c\xcbH\xcd\xc9\xc9\x07\x00\x06,\x02\x15')
    self.assertTrue(req.Enabled())
    self.assertEqual('hello', req.Text())
    req.Load('bye bye')
    self.assertEqual('POST / HTTP/1.1\r\n\r\n' +
        'x\x9cK\xaaLUH\xaaL\x05\x00\n\x81\x02\xa1', req.String())


class TestResponse(unittest.TestCase):

  def testDisabled(self):
    resp = zlibedit.Response.Parse('HTTP/1.1 200 OK\r\n\r\n<not>')
    self.assertFalse(resp.Enabled())

  def testDecode(self):
    resp = zlibedit.Response.Parse('HTTP/1.1 200 OK\r\n\r\n' + 
        'x\x9c+\xcf/\xca.\x06\x00\x06\xb3\x027')
    self.assertTrue(resp.Enabled())
    self.assertEqual('works', resp.Text())


if __name__ == '__main__':
    unittest.main()
