# -*- coding: utf-8 -*-

from Cocoa import NSAlert, NSTextField
from Foundation import NSString, NSMakeRect

def input_box(title):
    box = NSAlert.alloc().init()
    box.addButtonWithTitle_(NSString.alloc().initWithString_("OK"))
    box.setMessageText_(NSString.alloc().initWithString_(title))
    textbox = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 200, 24));
    box.setAccessoryView_(textbox)
    box.runModal()
    return textbox.stringValue()
