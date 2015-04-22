"""Burp editor extension example: library to edit user agent.

This silly user agent editor demonstrates how to make a Burp editor extension.
The Request/Response extend classes from the http library which does the
parsing for us so we can focus on defining the extension methods.
"""

# https://github.com/StalkR/misc/blob/master/burp/http.py
import http

# Extension name and tab title
NAME = 'User-Agent editor'
TITLE = 'UA'


class Request(http.Request):

  def Enabled(self):
    """Returns whether this request should enable the editor (bool)."""
    return bool(self.Headers.Get('User-Agent'))

  def Text(self):
    """Returns text for the editor."""
    return self.Headers.Get('User-Agent')

  def Load(self, text):
    """Reconstruct the request (self) from the modified text."""
    self.Headers.Set('User-Agent', text)


class Response(http.Response):

  def Enabled(self):
    """Returns whether this request should enable the editor (bool)."""
    return False  # servers do not have user agents so always disabled
    
  def Text(self):
    """Returns text for the editor."""
    return ''
