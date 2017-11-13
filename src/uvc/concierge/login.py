# -*- coding: utf-8 -*-

import gevent
from gevent import Greenlet
from webob import Response, Request
from webob.exc import HTTPFound
from repoze.who.api import get_api
from . import PORTALS_REGISTRY
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


def initiate_session(environ, username, domains):
    print( "I SET THE SESSION" )
    session = environ.get('beaker.session')
    if session and not 'address' in session:
        session['address'] = dict(name1="Novareto", name2="GMBH", strasse="Karolinenstr. 17", plz="90619", ort=u"Fürth")
        session.save()
        session.persist()


@implementer(IAuthenticator)
class PortalsLoginPlugin(object):

    def try_login(self, username, password):
        queriers = {}
        successes = set()
        for name, app in PORTALS_REGISTRY.items():
            print(app)
            method = getattr(app, 'login_method', 'default')
            if method is not None:
                querier = METHODS.get(method)
                if querier is not None:
                    url = getattr(app, 'login_url', None)
                    queriers[name] = pool.apply_async(
                        check_auth, (querier, url, username, password))
                else:
                    print("Login couldn't be attempted on portal : %s. Login method `%s` is unknown" % (name, method))

        for name, task in queriers.items():
            try:
                success = task.get(timeout=3)
                print ("success %s" % success)
                #if success == 1:
                #    print "Successfuly authenticated on %r" % name
                if success is True:
                    #print "Successfuly authenticated on %r" % name
                    successes.add(name)
                else:
                    print ("LOGNI FAILED ON %r" % name)
                    pass
                    #print "Login failed on %r" % name
            except TimeoutError:
                print( "Timeout while trying to login on %r" % name)
        return successes

    def authenticate(self, environ, identity):
        """Return username or None.
        """
        try:
            username = identity['login']
            password = identity['password']
        except KeyError:
            return None

        successes = self.try_login(username, password)
        if successes:
            thread = Greenlet.spawn(
                initiate_session, environ, username, successes)
            gevent.joinall([thread])
            environ['remote.domains'] = successes
            return username
        return None


def logout_app(environ, start_response):
    who_api = get_api(environ)
    headers = who_api.logout()
    session = environ['beaker.session']
    session.invalidate()
    return HTTPFound(location='/login', headers=headers)(
        environ, start_response)


def login_center(environ, start_response):
    request = Request(environ)
    response = LoginForm(environ, request)()
    response.headers['Cache-Control'] = "no-cache"
    return response(environ, start_response)
