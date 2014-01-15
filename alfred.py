import plistlib
import os.path
import xml.etree.ElementTree as ET

preferences = plistlib.readPlist('info.plist')
bundle_id = preferences['bundleid']

class Feedback(object):
  def __init__(self):
    self.items = []

  def append_item(self, **kwargs):
    self.items.append(FeedbackItem(**kwargs))

  def xml(self):
    items_xml = ET.Element('items')
    for item in self.items:
      item_xml = ET.SubElement(items_xml, 'item')
      item_xml.set('uid', item.uid)
      item_xml.set('arg', item.arg)
      item_xml.set('valid', item.valid)
      item_title_xml = ET.SubElement(item_xml, 'title')
      item_title_xml.text = item.title
      item_icon_xml = ET.SubElement(item_xml, 'icon')
      item_icon_xml.text = 'repo.png' # One day it'll be owner's avatar
    return ET.tostring(items_xml)

class FeedbackItem(object):
  def __init__(self, uid, title, arg, valid='yes'):
    self.uid = uid
    self.title = title
    self.arg = arg
    self.valid = valid

def store(volatile=True):
    path = {
        True: '~/Library/Caches/com.runningwithcrayons.Alfred-2/Workflow Data',
        False: '~/Library/Application Support/Alfred 2/Workflow Data'
    }[bool(volatile)]
    store_path = os.path.join(os.path.expanduser(path), bundle_id)
    if not os.path.isdir(store_path):
      os.mkdir(store_path)
    return store_path

