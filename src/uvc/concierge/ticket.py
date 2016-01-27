# -*- coding: utf-8 -*-

import hashlib
import base64
import hmac
import os

from urllib import unquote
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto.Signature import PKCS1_v1_5
from repoze.who._compat import STRING_TYPES
from repoze.who._compat import get_cookies
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin as Basetkt


SESSION_KEY = "remote"


class MissingTicket(Exception):
    title = u'Security ticket is missing : access forbidden'


class TicketParseError(Exception):
    """Base class for all ticket parsing errors"""

    def __init__(self, ticket, msg=''):
        self.ticket = ticket
        self.msg = msg

    def __str__(self):
        return 'Ticket parse error: %s (%s)' % (self.msg, self.ticket)


class BadTicket(TicketParseError):

    def __init__(self, ticket, msg='Invalid ticket format'):
        super(BadTicket, self).__init__(ticket, msg)


class BadSignature(TicketParseError):

    def __init__(self, ticket, msg='Invalid ticket format'):
        super(BadSignature, self).__init__(ticket, msg)


def read_key(path, passphrase=None):
    with open(path, "r") as kd:
        if passphrase is not None:
            key = RSA.importKey(kd, passphrase=passphrase)
        else:
            key = RSA.importKey(kd)
    return key


class AESCipher(object):

    def __init__(self, key):
        self.key = key

    @staticmethod
    def pkcs1_pad(data):
        length = AES.block_size - (len(data) % AES.block_size)
        return data + ('\0' * length)

    @staticmethod
    def pkcs1_unpad(data):
        return data.rstrip('\0')

    @staticmethod
    def pkcs7_pad(data):
        length = AES.block_size - (len(data) % AES.block_size)
        return data + (chr(length) * length)

    @staticmethod
    def pkcs7_unpad(data):
        return data[:-ord(data[-1])]

    def encrypt(self, data):
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        length = AES.block_size - (len(data) % AES.block_size)
        encrypted = iv + cipher.encrypt(self.pkcs1_pad(data))
        return encrypted

    def decrypt(self, data):
        iv = data[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decoded = cipher.decrypt(data[AES.block_size:])
        return self.pkcs1_unpad(decoded)


def calculate_digest(privkey, data):
    dgst = SHA.new(data)
    pkcs = PKCS1_v1_5.new(privkey)
    sig = pkcs.sign(dgst)
    return base64.b64encode(sig)


def verify_sig(pubkey, data, sig):
    sig = base64.b64decode(sig)
    dgst = SHA.new(data)
    verifier = PKCS1_v1_5.new(pubkey)
    return verifier.verify(dgst, sig)


def parse_ticket(ticket, pubkey):
    i = ticket.rfind(';')
    sig = ticket[i+1:]
    if sig[:4] != 'sig=':
        raise BadTicket(ticket)

    sig = sig[4:]
    data = ticket[:i]

    if not verify_sig(pubkey, data, sig):
        raise BadSignature(ticket)

    try:
        fields = dict(f.split('=', 1) for f in data.split(';'))
    except ValueError:
        raise BadTicket(ticket)

    if 'uid' not in fields:
        raise BadTicket(ticket, 'uid field required')

    if 'validuntil' not in fields:
        raise BadTicket(ticket, 'validuntil field required')

    try:
        fields['validuntil'] = int(fields['validuntil'])
    except ValueError:
        raise BadTicket(ticket, 'Bad value for validuntil field')

    if 'tokens' in fields:
        tokens = fields['tokens'].split(',')
        if tokens == ['']:
            tokens = []
        fields['tokens'] = tokens
    else:
        fields['tokens'] = []

    if 'graceperiod' in fields:
        try:
            fields['graceperiod'] = int(fields['graceperiod'])
        except ValueError:
            raise BadTicket(ticket, 'Bad value for graceperiod field')

    return fields


def create_ticket(privkey, uid, validuntil, ip=None, tokens=(),
                  udata='', graceperiod=None, extra_fields = ()):
    """Returns signed mod_auth_pubtkt ticket.

    Mandatory arguments:

    ``privkey``:
    Private key object. It must be Crypto.PublicKey.RSA

    ``uid``:
    The user ID. String value 32 chars max.

    ``validuntil``:
    A unix timestamp that describe when this ticket will expire. Integer value.

    Optional arguments:

    ``ip``:
    The IP address of the client that the ticket has been issued for.

    ``tokens``:
    List of authorization tokens.

    ``udata``:
    Misc user data.

    ``graceperiod``:
    A unix timestamp after which GET requests will be redirected to refresh URL.

    ``extra_fields``:
    List of (field_name, field_value) pairs which contains addtional, non-standa
rd fields.
    """

    v = 'uid=%s;validuntil=%d' % (uid, validuntil)
    if ip:
        v += ';cip=%s' % ip
    if tokens:
        v += ';tokens=%s' % ','.join(tokens)
    if graceperiod:
        v += ';graceperiod=%d' % graceperiod
    if udata:
        v += ';udata=%s' % udata
    for k,fv in extra_fields:
        v += ';%s=%s' % (k,fv)
    v += ';sig=%s' % calculate_digest(privkey, v)
    return v


def cipher(app, global_conf, cipher_key=None):
    def cipher_layer(environ, start_response):
        environ['aes_cipher'] = AESCipher(cipher_key)
        return app(environ, start_response)
    return cipher_layer


def bauth(aes, val):
    return aes.encrypt(val)


def read_bauth(aes, val):
    return aes.decrypt(base64.b64decode(val))


class AuthTktCookiePlugin(Basetkt):

    def __init__(self, secret, cookie_name='auth_tkt',
                 secure=False, include_ip=False, timeout=None,
                 reissue_time=None, userid_checker=None, pkey=None):
        Basetkt.__init__(self, secret, cookie_name, secure, include_ip,
                         timeout, reissue_time, userid_checker)
        self.pkey = pkey
    
    def remember(self, environ, identity):
        cookies = get_cookies(environ)
        if identity is not None and not self.cookie_name in cookies:
            aes = environ['aes_cipher']
            val = base64.b64encode(bauth(aes, '%s:%s' % (
                identity['login'], identity['password'])))
            identity['tokens'] = environ['remote.domains']
            identity['repoze.who.userid'] = val 
        return Basetkt.remember(self, environ, identity)
        

def _bool(value):
    if isinstance(value, STRING_TYPES):
        return value.lower() in ('yes', 'true', '1')
    return value

    
def make_plugin(secret=None,
                secretfile=None,
                cookie_name='auth_tkt',
                secure=False,
                include_ip=False,
                timeout=None,
                reissue_time=None,
                userid_checker=None,
                pkey=None,
               ):
    from repoze.who.utils import resolveDotted
    if (secret is None and secretfile is None):
        raise ValueError("One of 'secret' or 'secretfile' must not be None.")
    if (secret is not None and secretfile is not None):
        raise ValueError("Specify only one of 'secret' or 'secretfile'.")
    if secretfile:
        secretfile = os.path.abspath(os.path.expanduser(secretfile))
        if not os.path.exists(secretfile):
            raise ValueError("No such 'secretfile': %s" % secretfile)
        with open(secretfile) as f:
            secret = f.read().strip()
    if timeout:
        timeout = int(timeout)
    if reissue_time:
        reissue_time = int(reissue_time)
    if userid_checker is not None:
        userid_checker = resolveDotted(userid_checker)
    plugin = AuthTktCookiePlugin(secret,
                                 cookie_name,
                                 _bool(secure),
                                 _bool(include_ip),
                                 timeout,
                                 reissue_time,
                                 userid_checker,
                                 pkey=pkey,
                                 )
    return plugin
