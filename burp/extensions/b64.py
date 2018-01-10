"""Burp base64 editor library to see and edit base64 data.

The Request/Response extend classes from the http library which does the
parsing for us so we can focus on the extension logic.
"""

import base64
import re

# https://github.com/StalkR/misc/blob/master/burp/http.py
import http

# Extension name and tab title
NAME = 'Base64 editor'
TITLE = 'B64'


class Request(http.Request):

  def Enabled(self):
    """Returns whether this request should enable the editor (bool)."""
    return bool(re.match(r'^[-A-Za-z0-9+/=]+$', self.Body))

  def Text(self):
    """Returns text for the editor."""
    return base64.b64decode(self.Body)

  def Load(self, text):
    """Reconstruct the request (self) from the modified text."""
    self.Body = base64.b64encode(text)


class Response(http.Response):

  def Enabled(self):
    """Returns whether this request should enable the editor (bool)."""
    return bool(re.match(r'^[-A-Za-z0-9+/=]+$', self.Body))
    
  def Text(self):
    """Returns text for the editor."""
    return base64.b64decode(self.Body)
