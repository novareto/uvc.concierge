# -*- coding: utf-8 -*-

from os import path
from dolmen.template.components import TALTemplate
from webob import Response, Request
from webob.exc import HTTPFound
from repoze.who.api import get_api


template_dir = path.dirname(__file__)
login_template = path.join(template_dir, 'login.pt')

SUCCESS = object()
FAILURE = object()


class LogMe(object):

    def __init__(self, context, environ, request):
        self.context = context
        self.environ = environ
        self.request = request

    def extract(self):
        return {
            'login': self.request.POST['login'],
            'password': self.request.POST['password'],
        }

    def __call__(self):
        data = self.extract()

        if not data or not data['login'] or not data['password']:
            return FAILURE, [], data

        who_api = get_api(self.environ)
        self.environ['remote.hub'] = self.context
        authenticated, headers = who_api.login(data)
        
        if authenticated:
            return SUCCESS, headers, data
        else:
            _, headers = who_api.login({})

        self.request.response_headerlist = headers
        if 'REMOTE_USER' in self.request.environ:
            del self.request.environ['REMOTE_USER']

        return FAILURE, headers, data


class LoginForm(object):

    template = TALTemplate(filename=login_template)
    actions = {
        'action.login': LogMe,
    }

    def __init__(self, context, environ, request):
        self.context = context
        self.environ = environ
        self.request = request

    def render(self, message, data):
        return self.template.render(self, **{
            'action': '/login',
            'message': message,
            'data': data,
        })

    def update(self):
        identity = self.environ.get('repoze.who.identity')
        if identity is not None:
            response = Response()
            came_from = self.request.GET.get('came_from', '/')
            if came_from:
                response.status = '304 Not Modified'
                response.location = str(came_from)
                return response
        return None

    def __call__(self):
        response = self.update()
        if response is not None:
            return response
        
        success = None
        headers = []
        message = ''
        data = {}
        
        for action, trigger in self.actions.items():
            if action in self.request.POST:
                success, headers, data = trigger(
                    self.context, self.environ, self.request)()
                if success == SUCCESS:
                    return HTTPFound(location='/', headers=headers)
                if success == FAILURE:
                    if not headers:
                        message = u"Missing info."
                    else:
                        message = u"Login failed."
                break
        html = self.render(message, data)
        return Response(html, headers=headers)
