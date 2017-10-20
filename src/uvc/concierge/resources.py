# -*- coding: utf-8 -*-

from fanstatic import Library, Resource
#from js.jquery import jquery

library = Library('remote_wsgi', 'concierge_client')
js = Resource(library, 'dist/build.js', bottom=True)
