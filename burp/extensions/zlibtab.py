"""Burp zlib editor library to see and edit zlib data.

The Request/Response extend classes from the http library which does the
parsing for us so we can focus on the extension logic.
"""

import zlib

# https://github.com/StalkR/misc/blob/master/burp/http.py
import http

# Extension name and tab title
NAME = 'Zlib tab'
TITLE = 'Zlib'


class Request(http.Request):

  def Enabled(self):
    """Returns whether this request should enable the editor (bool)."""
    # https://stackoverflow.com/questions/9050260/what-does-a-zlib-header-look-like
    return self.Body.startswith('\x78')

  def Text(self):
    """Returns text for the editor."""
    return zlib.decompress(self.Body)

  def Load(self, text):
    """Reconstruct the request (self) from the modified text."""
    self.Body = zlib.compress(text)


class Response(http.Response):

  def Enabled(self):
    """Returns whether this request should enable the editor (bool)."""
    # https://stackoverflow.com/questions/9050260/what-does-a-zlib-header-look-like
    return self.Body.startswith('\x78')
    
  def Text(self):
    """Returns text for the editor."""
    return zlib.decompress(self.Body)
