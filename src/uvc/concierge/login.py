# -*- coding: utf-8 -*-

from webob import Response, Request
from webob.exc import HTTPFound
from repoze.who.api import get_api
from .portals import XMLRPCPortal, JSONPortal
from .forms import LoginForm
from repoze.who.interfaces import IAuthenticator, IMetadataProvider
from zope.interface import implementer
from multiprocessing.pool import ThreadPool
from multiprocessing import TimeoutError


pool = ThreadPool(processes=4)


def check_auth(querier, url, username, password):
    try:
        return querier(url).check_authentication(
            username, password)
    except Exception:
        return False


METHODS = {
    'json': JSONPortal,
    'xmlrpc': XMLRPCPortal,
    }


@implementer(IAuthenticator)
class PortalsLoginPlugin(object):

    def try_login(self, hub, username, password):
        queriers = {}
        successes = set()
        for path_info, app in hub.applications:
            method = getattr(app, 'login_method', None)
            if method is not None:
                querier = METHODS.get(method)
                if querier is not None:
                    _, script_name = path_info
                    url = getattr(app, 'login_url', None)
                    queriers[script_name] = pool.apply_async(
                        check_auth, (querier, url, username, password))

        for name, task in queriers.items():
            try:
                success = task.get(timeout=3)
                if success is True:
                    print "Successfuly authenticated on %r" % name
                    successes.add(script_name)
                else:
                    print "Login failed on %r" % name
            except TimeoutError:
                print "Timeout while trying to login on %r" % name
        return successes

    def authenticate(self, environ, identity):
        """Return username or None.
        """
        try:
            username = identity['login']
            password = identity['password']
            hub = environ['remote.hub']
        except KeyError:
            return None

        successes = self.try_login(hub, username, password)
        if successes:
            environ['remote.domains'] = successes
            return username
        return None


def logout_app(environ, start_response):
    who_api = get_api(environ)
    headers = who_api.logout()
    return HTTPFound(location='/login', headers=headers)(
                    environ, start_response)


def login_center(hub):
    def login_view(environ, start_response):
        request = Request(environ)
        response = LoginForm(hub, environ, request)()
        return response(environ, start_response)
    return login_view
