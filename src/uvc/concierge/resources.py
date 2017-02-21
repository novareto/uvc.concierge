# -*- coding: utf-8 -*-

from fanstatic import Library, Resource
from js.jquery import jquery

library = Library('remote_wsgi', 'assets')
js = Resource(library, 'menu.js', depends=[jquery])
css = Resource(library, 'menu.css')

js = Resource(library, 'main.c5596499.js', bottom=True)
css = Resource(library, 'main.65027555.css')
