"""Burp zlib editor extension to see and edit zlib data."""

from burp import IBurpExtender
from burp import IMessageEditorTabFactory
from burp import IMessageEditorTab

import zlibtab as editor


class BurpExtender(IBurpExtender, IMessageEditorTabFactory):

  def registerExtenderCallbacks(self, callbacks):
    self.callbacks = callbacks
    callbacks.setExtensionName(editor.NAME)
    callbacks.registerMessageEditorTabFactory(self)

  def createNewInstance(self, controller, editable):
    return EditorTab(self, controller, editable)


class EditorTab(IMessageEditorTab):

  def __init__(self, extender, controller, editable):
    self.editor = extender.callbacks.createTextEditor()
    self.editor.setEditable(editable)

  def getTabCaption(self):
    return editor.TITLE

  def getUiComponent(self):
    return self.editor.getComponent()

  def isEnabled(self, content, isRequest):
    s = content.tostring()
    r = editor.Request.Parse(s) if isRequest else editor.Response.Parse(s)
    return r.Enabled() if r else False

  def setMessage(self, content, isRequest):
    if not content:
      return
    s = content.tostring()
    r = editor.Request.Parse(s) if isRequest else editor.Response.Parse(s)
    self.editor.setText(r.Text())
    self.r = r

  def getMessage(self):
    if not self.editor.isTextModified():
      return self.editor.getText()
    # we rely on setMessage being called before to set self.r
    self.r.Load(self.editor.getText().tostring())
    return self.r.String()

  def isModified(self):
    return self.editor.isTextModified()

  def getSelectedData(self):
    return self.editor.getSelectedText()
