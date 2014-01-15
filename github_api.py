import httplib
import json
import alfred
import sqlite3
import os
import os.path

class RequestCache(object):
  def __init__(self, db):
    self.connection = sqlite3.connect(db)
    self.connection.text_factory = str
    self.cursor = self.connection.cursor()
    self.__init_schema__()

  def __init_schema__(self):
    self.cursor.execute('CREATE TABLE IF NOT EXISTS requests(request, etag, contents)')

  def get_cache(self, req):
    self.cursor.execute('SELECT * FROM requests WHERE request = ?', [req])
    return self.cursor.fetchone()

  def set_cache(self, req, etag, contents):
    self.cursor.execute('INSERT INTO requests(request, etag, contents) VALUES (?, ?, ?)', [req, etag, contents])
    self.connection.commit()

class Request(object):
  def __init__(self, lazy=True, debug=False):
    self.req_cache = RequestCache(os.path.join(alfred.store(), 'github.db'))
    self.lazy = lazy
    self.debug = debug

  def request(self, req):
    cached_req, cached_etag, cached_contents = self.req_cache.get_cache(req) or (None, None, None)
    if cached_contents and self.lazy:
      self.__dbg__('lazy mode, for ' + req + ' returning cached contents')
      return json.loads(cached_contents)

    conn = httplib.HTTPSConnection('api.github.com', 443)
    conn.putrequest('GET', req)
    conn.putheader('Authorization', 'token ' + os.environ['ALFRED_GITHUB_TOKEN'])
    conn.putheader('User-Agent', 'Alfred Github')
    if cached_req:
      self.__dbg__('cached: req: ' + cached_req + ' etag: ' + cached_etag + ' contents: ' + cached_contents)
      conn.putheader('If-None-Match', cached_etag)
    conn.endheaders()
    r = conn.getresponse()
    raw_response_contents = ''
    if r.getheader('status') == '304 Not Modified':
      self.__dbg__('Using cached')
      raw_response_contents = cached_contents
    elif r.getheader('status') == '200 OK':
      self.__dbg__('Getting afresh')
      raw_response_contents = r.read()
      etag = r.getheader('etag')
      self.__dbg__('new etag ' + etag)
      self.req_cache.set_cache(req, etag, raw_response_contents)
    else:
      self.__dbg__('shite...')
    return json.loads(raw_response_contents)

  def __dbg__(self, msg):
    if self.debug:
      print(msg)

