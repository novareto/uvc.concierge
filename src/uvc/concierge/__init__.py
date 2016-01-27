# -*- coding: utf-8 -*-

import json
import base64
from wsgiproxy.app import WSGIProxyApp
from paste.urlmap import URLMap, parse_path_expression
from repoze.who.api import get_api
from .resources import js, css
from .login import logout_app, login_center
from .ticket import read_bauth


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


def wrap_start_response(start_response):
    def wrapped_start_response(status, headers_out):
        # Remove "hop-by-hop" headers
        headers_out = [(k,v) for (k,v) in headers_out
                       if k not in FILTER_HEADERS]
        return start_response(status, headers_out)
    return wrapped_start_response


def lister(value):
    if value is None:
        return None
    if isinstance(value, (list, set, tuple)):
        return value
    return [v.strip() for v in value.split(',')]


def wrapper(app):
    def caller(environ, start_response):
        js.need()
        css.need()
        if 'repoze.who.identity' in environ:
            aes = environ['aes_cipher']
            val = environ['repoze.who.identity']['repoze.who.userid']
            userpwd = read_bauth(aes, val)
            httpauth = 'Basic ' + base64.encodestring(userpwd).strip()
            environ['HTTP_AUTHORIZATION'] = httpauth
            
        if app.use_x_headers is True:
            environ['HTTP_X_VHM_HOST'] = app.href
            environ['HTTP_X_VHM_ROOT'] = app.target

        return app(environ, wrap_start_response(start_response))
    return caller


def hub_factory(loader, global_conf, **local_conf):
    if 'not_found_app' in local_conf:
        not_found_app = local_conf.pop('not_found_app')
    else:
        not_found_app = global_conf.get('not_found_app')
    if not_found_app:
        not_found_app = loader.get_app(not_found_app, global_conf=global_conf)
    urlmap = RemoteHub(not_found_app=not_found_app)
    for path, app_name in local_conf.items():
        path = parse_path_expression(path)
        app = loader.get_app(app_name, global_conf=global_conf)
        urlmap[path] = app
    return urlmap


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
        return [response_body]


class RemoteHub(URLMap):

    def about(self, environ):
        identity = environ.get('repoze.who.identity')
        if identity is not None:
            tokens = set(identity.get('tokens', []))
            for (domain, app_url), app in self.applications:
                if app_url in tokens:
                    link_url = app.link_url
                    if link_url is None:
                        link_url = 'http://%s%s' % (
                            environ['HTTP_HOST'], app_url)
                    yield (link_url, app.title)

    def __init__(self, *args, **kwargs):
        URLMap.__init__(self, *args, **kwargs)
        self['/__about__'] = HubDetails(self)
        self['/login'] = login_center(self)
        self['/logout'] = logout_app


def make_proxy(*global_conf, **local_conf):
    href = local_conf.get('href')
    secret_file = local_conf.get('secret_file')
    string_keys = lister(local_conf.get('string_keys'))
    unicode_keys = lister(local_conf.get('unicode_keys'))
    json_keys = lister(local_conf.get('json_keys'))
    pickle_keys = lister(local_conf.get('pickle_keys'))
    
    application = WSGIProxyApp(
        href,
        secret_file=secret_file,
        string_keys=string_keys,
        unicode_keys=unicode_keys,
        json_keys=json_keys,
        pickle_keys=pickle_keys,
    )
    application.href = href
    application.target = local_conf.get('target', '/')
    application.use_x_headers = local_conf.get(
        'use_x_headers', 'False').lower() == 'true'

    app = wrapper(application)

    # login info & metadata
    app.login_method = local_conf.get('login_method')
    app.login_url = local_conf.get('login_url') or href
    app.title = local_conf.get('title') or 'No title'
    app.link_url = local_conf.get('link_url', None)

    return app
