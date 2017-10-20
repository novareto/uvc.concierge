# -*- coding: utf-8 -*-

import json
import base64
import gevent

from paste.urlmap import URLMap, parse_path_expression
from repoze.who.api import get_api
from .resources import js
from .login import logout_app, login_center
from .ticket import read_bauth
from .injector import ConciergeKey
from .websockets.websocket import WebSocketWSGI
from .websockets.app import handle


FILTER_HEADERS = [
    'Connection',
    'Keep-Alive',
    'Proxy-Authenticate',
    'Proxy-Authorization',
    'TE',
    'Trailers',
    'Transfer-Encoding',
    'Upgrade',
    ]


#def wrap_start_response(start_response):
#    def wrapped_start_response(status, headers_out):
#        # Remove "hop-by-hop" headers        
#        keep = [(header, value) for (header, value) in headers_out
#                if header not in FILTER_HEADERS]
#        if header == 'Content-Type' and 'text/html' in value:
#        return start_response(status, keep)
#    return wrapped_start_response


def wrap_start_response(start_response):
    def wrapped_start_response(status, headers_out):
        keep = []
        # Remove "hop-by-hop" headers
        for header, value in headers_out:
            if header not in FILTER_HEADERS:
                keep.append((header, value))
            if header == 'Content-Type' and 'text/html' in value:
                if status == "200 OK":
                    "NEEED ME"
                    js.need()
        return start_response(status, keep)
    return wrapped_start_response


def wrapper(hub, app):
    def caller(environ, start_response):

        environ['HUB'] = hub
        
        if 'repoze.who.identity' in environ:
            aes = environ['aes_cipher']
            val = environ['repoze.who.identity']['repoze.who.userid']
            userpwd = read_bauth(aes, val)
            httpauth = b'Basic ' + base64.encodestring(userpwd).strip()
            environ['HTTP_AUTHORIZATION'] = httpauth
            
        if app.use_x_headers is True:
            print("we use it ?")
            environ['HTTP_X_VHM_HOST'] = "karl.novareto.de:8000" #app.host
            environ['VHM_ROOT'] = "plone" #app.target

        environ['RAW_URI'] = environ['RAW_URI'].replace('/plone', '')
        print(environ['RAW_URI'])
        environ['RAW_URI'] = environ['RAW_URI'].replace('/uvcsite', '')
        result = ConciergeKey(app)(environ, wrap_start_response(start_response))

        return result
    return caller


class HubDetails(object):

    def __init__(self, hub):
        self.hub = hub

    def __call__(self, environ, start_response):
        result = dict(self.hub.about(environ))
        response_body = json.dumps(result)
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json'),
                            ('Content-Length', str(len(response_body)))]
        start_response(status, response_headers)
        return [bytes(response_body, 'utf8')]


def make_listener(*global_conf, **local_conf):

    import os
    def app(environ, start_response):
        data = open(os.path.join(
                     os.path.dirname(__file__),
                     'websocket.html')).read()
        data = data % environ
        start_response('200 OK', [('Content-Type', 'text/html'),
                                  ('Content-Length',  str(len(data)))])
        return [data.encode('utf-8')]

    return app
