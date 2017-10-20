# -*- coding: utf-8 -*-

import os
import sys
import webob

if sys.version_info[0] < 3:
    as_bytestring = lambda x: x
else:
    as_bytestring = lambda x: x.encode('utf-8')


CONTENT_TYPES = frozenset((
    'text/html',
    'text/xml',
    'application/xhtml+xml',
))

CSS = """
<style type="text/css" media="screen">
  #remotewsgi {
    position: fixed;
    top: 0px;
    background-color: black;
    z-index: 1100;
    margin: 0;
    list-style: none;
    height: 30px;
    line-height: 30px;
    width: 100%;
  }

  #remotewsgi li {
    display: inline-block;
  }

  #remotewsgi a {
    color: white;
  }

  html > body.site-siguvportal {
    margin-top: 30px !important;
  }

</style>
"""

with open(os.path.join(os.path.dirname(__file__), 'nav.pt'), 'r') as tpl:
    VUE = tpl.read()


class ConciergeKey(object):

    def about(self, environ):
        host = environ.get('HTTP_X_VHM_HOST') or environ.get('HTTP_HOST')
        identity = environ.get('repoze.who.identity')
        if identity is not None:
            tokens = set(identity.get('tokens', []))
            for (domain, app_url), app in environ['HUB'].applications:
                if app_url in tokens:
                    link_url = app.link_url
                    if link_url is None:
                        link_url = 'http://%s%s' % (host, app_url)
                    yield (link_url, app.title)
            link_url = 'http://%s/logout' % host
            yield (link_url, "Logout")
        else:
            link_url = 'http://%s/login' % host
            yield (link_url, "Login")

    def render(self, environ):
        #html = "<ul id='remotewsgi' class='list'>%s</ul>"
        #html = html % ('\n'.join(
        #    ("<li><a href='%s'> 🔓 %s </a></li>" % (url, title)
        #     for url, title in self.about(environ))))
        # return html
        return VUE

    def __init__(self, app, **config):
        self.app = app

    def __call__(self, environ, start_response):
        request = webob.Request(environ)

        # We only continue if the request method is appropriate.
        if not request.method in ['GET', 'POST', 'HEAD']:
            return self.app(environ, start_response)

        # Get the response from the wrapped application:
        response = request.get_response(self.app)

        # We only continue if the content-type is appropriate.
        if not (response.content_type and
                response.content_type.lower() in CONTENT_TYPES):
            return response(environ, start_response)

        # HTML injection
        menu = self.render(environ)        
        html = response.body.replace(
            as_bytestring('</body>'),
            as_bytestring('%s</body>' % menu), 1)

        # CSS injection
        html = html.replace(
            as_bytestring('</head>'),
            as_bytestring('%s</head>' % CSS), 1)

        # Replacing the body
        response.body = b''
        response.write(html)

        # Something was injected, No cache.
        response.headers['Cache-Control'] = "no-cache"
        
        return response(environ, start_response)
