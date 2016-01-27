# -*- coding: utf-8 -*-

from fanstatic import Library, Resource
from js.jquery import jquery

library = Library('remote_wsgi', 'assets')
js = Resource(library, 'menu.js', depends=[jquery])
css = Resource(library, 'menu.css')
