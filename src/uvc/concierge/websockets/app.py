# -*- coding: utf-8 -*-

from urllib import parse
import json
from repoze.who.api import get_api


MALFORMED = [
    "client_error", {'message': 'Server was unable to read the command.'}]

UNKNOWN_COMMAND = [
    "client_error", {'message': 'Command is unknown.'}]



def about(environ):
    hub = environ['remote.hub']
    identity = environ.get('repoze.who.identity')
    if identity is not None:
        tokens = set(identity.get('tokens', []))
        for (domain, app_url), app in hub.applications:
            if app_url in tokens:
                link_url = app.link_url
                if link_url is None:
                    link_url = 'http://%s%s' % (
                        environ['HTTP_HOST'], app_url)
                yield (link_url, app.title)
        link_url = u'http://%s/logout' % environ['HTTP_HOST']
        yield (link_url, u"Logout")
    else:
        link_url = u'http://%s/login' % environ['HTTP_HOST']
        yield (link_url, u"Login")


def Login(ws, formdata):

    identity = ws.environ.get('repoze.who.identity')
    if identity is None:
        if ('login' in formdata) ^ ('password' in formdata):
            return ["login_error", {'message': 'missing data'}]
        who_api = get_api(ws.environ)    
        identity, headers = who_api.login(formdata)

        if identity is not None:
            identifiers = dict(who_api.identifiers)
            auth_tkt = identifiers['auth_tkt']
            auth_tkt.remember(ws.environ, identity)
            ws.environ['repoze.who.identity'] = identity
            return ["login_success", {
                'data': headers, 'menu': list(about(ws.environ))}]
        else:
            return ["login_failure", {'message': 'Login failed'}]
    else:
        return ["already_logged_in", {
            'menu': list(about(ws.environ))}]


def isLoggedIn(ws, formdata):
    identity = ws.environ.get('repoze.who.identity')
    if identity:
        print("YES I AM LOGGGEED")
        return ["already_logged_in", {
            'menu': list(about(ws.environ))}]
    return ["not_logged_in"]

DISPATCHER = {
    'login': Login,
    'isloggedin': isLoggedIn
    }


def handle(ws):
    while True:
        m = ws.wait()
        if m is None:
            break

        try:
            message = json.loads(str(m, 'utf-8'))
            print (message)
            command, data = message
            print (command)
            print (data)
        except ValueError:
            result = MALFORMED
        else:
            handler = DISPATCHER.get(command)
            if handler is not None:
                result = handler(ws, data)
            else:
                result = UNKNOWN_COMMAND

        encoded = json.dumps(result)
        ws.send(encoded)
