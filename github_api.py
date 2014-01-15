# -*- coding: utf-8 -*-

from __future__ import print_function
import base64
import httplib
import json
import alfred
import sqlite3
import os.path
import sys

class RequestCache(object):
    def __init__(self, db):
        self.connection = sqlite3.connect(db)
        self.connection.text_factory = str
        self.cursor = self.connection.cursor()
        self.__init_schema__()

    def __init_schema__(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests(
                request PRIMARY KEY NOT NULL,
                etag,
                contents NOT NULL)
            """)

    def get_cache(self, req):
        self.cursor.execute('SELECT * FROM requests WHERE request = ?', [req])
        return self.cursor.fetchone()

    def set_cache(self, req, etag, contents):
        self.cursor.execute("""
            INSERT OR REPLACE INTO requests(request, etag, contents)
                VALUES (?, ?, ?)', [req, etag, contents])
            """)
        self.connection.commit()

class PlainRequest(object):
    def __init__(self, request_path, method='GET', debug=False):
        self.method = method
        self.request_path = request_path
        self.debug = debug

    def request(self):
        conn = httplib.HTTPSConnection('api.github.com', 443)
        if self.debug:
            conn.set_debuglevel(1)
        conn.putrequest(self.method, self.request_path)
        self.put_headers(conn)
        result = conn.getresponse()
        return self.process_response(result)

    def put_headers(self, conn):
        conn.putheader('User-Agent', 'Alfred Github')
        conn.endheaders()

    def process_response(self, response):
        raw_response_contents = response.read()
        return json.loads(raw_response_contents)

    def __dbg__(self, msg):
        if self.debug:
            print(msg, file=sys.stderr)

def token_authentication(request, token):
    if not token:
        raise KeyError('Token is required!')

    old_put_headers = request.put_headers
    def put_headers_with_token_authentication(self, conn):
        conn.putheader('Authorization', 'token ' + token)
        old_put_headers(conn)
    method = type(request.put_headers)
    request.put_headers = method(put_headers_with_token_authentication, request)
    return request

def basic_authentication(request, username, password):
    if not username or not password:
        raise KeyError('username and password are required!')

    old_put_headers = request.put_headers
    def put_headers_with_basic_authentication(self, conn):
        conn.putheader('Authorization', 'Basic ' + base64.b64encode(username + ':' + password))
        old_put_headers(conn)
    method = type(request.put_headers)
    request.put_headers = method(put_headers_with_basic_authentication, request)
    return request

def attach_json(request, data):
    if not data:
        raise KeyError('json data is required!')

    data = json.dumps(data)
    old_put_headers = request.put_headers
    def put_headers_with_json_data(self, conn):
        conn.putheader('Content-Type', 'application/json')
        conn.putheader('Content-Length', str(len(data)))
        old_put_headers(conn)
        conn.send(data)
    method = type(request.put_headers)
    request.put_headers = method(put_headers_with_json_data, request)
    return request

def cached_request(request, cache_store, lazy):
    if not cache_store:
        raise KeyError('cache_store is required!')

    cached_req, cached_etag, cached_contents = cache_store.get_cache(request.request_path) or (None, None, None)

    old_put_headers = request.put_headers
    def put_headers_with_cache(self, conn):
        if cached_req:
            self.__dbg__('Cache: will check with server')
            conn.putheader('If-None-Match', cached_etag)
        old_put_headers(conn)
    method = type(request.put_headers)
    request.put_headers = method(put_headers_with_cache, request)

    old_process_response = request.process_response
    def process_response_with_cache(self, response):
        raw_response_contents = ''
        if response.getheader('status') == '304 Not Modified':
            self.__dbg__('Cache: hit')
            raw_response_contents = cached_contents
        elif response.getheader('status') == '200 OK' or response.getheader('status') == '201 Created':
            self.__dbg__('Cache: update')
            raw_response_contents = response.read()
            etag = response.getheader('etag')
            cache_store.set_cache(self.request_path, etag, raw_response_contents)
        return json.loads(raw_response_contents)
    method = type(request.process_response)
    request.process_response = method(process_response_with_cache, request)

    old_request = request.request
    def request_with_caching(self):
        if cached_contents and lazy:
            self.__dbg__('Cache: force hit ' + self.request_path + ' (lazy)')
            return json.loads(cached_contents)
        return old_request()
    method = type(request.request)
    request.request = method(request_with_caching, request)
    return request

###### REQUESTS #####

def authorize(username, password, client_id, client_secret, scopes, note):
    data = {
             'client_secret': client_secret,
             'scopes': scopes,
             'note': note
           }
    request_path = '/authorizations/clients/' + client_id
    request = attach_json(
        basic_authentication(
            PlainRequest(method='PUT', request_path=request_path), username, password), data)
    result = request.request()
    return result['token']

class AuthenticatedGithub(object):
    def __init__(self, token, lazy=False, debug=False):
        self.token = token
        self.lazy = lazy
        self.debug = debug
        self.cache_store = RequestCache(alfred.store('github.db'))

    def get_orgs(self):
        return self.__get__('/user/orgs')

    def get_org_repos(self, org):
        return self.__get__('/orgs/' + org + '/repos?per_page=100')

    def get_own_repos(self):
        return self.__get__('/user/repos?per_page=100')

    def __get__(self, request_path):
        request = cached_request(
            token_authentication(
              PlainRequest(request_path, debug=self.debug), self.token), self.cache_store, lazy=self.lazy)
        return request.request()

