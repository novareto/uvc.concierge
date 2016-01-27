# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def text(path):
    with open(path) as f:
        text = f.read()
    return text

version = '0.1'
readme = text(os.path.join('src', 'uvc', 'concierge', 'README.txt'))
history = text(os.path.join('docs', 'HISTORY.txt'))

install_requires = [
    'PyCrypto',
    'barrel',
    'fanstatic',
    'js.jquery',
    'wsgiproxy',
    'zope.interface',
    'repoze.who',
    'requests',
    'dolmen.template[cromlech]',
    ]

tests_require = [
    ]

setup(name='uvc.concierge',
      version=version,
      description="Proxied WSGI Applications HUB",
      long_description="%s\n\n%s" % (readme, history),
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='UVC',
      author='The Dolmen team',
      author_email='dolmen@list.dolmen-project.org',
      url='http://gitweb.dolmen-project.org/',
      license='ZPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['uvc'],
      include_package_data=True,
      zip_safe=False,
      tests_require=tests_require,
      install_requires=install_requires,
      extras_require={'test': tests_require},
      entry_points={
          'paste.composite_factory': [
              'remotehub = uvc.concierge:hub_factory',
          ],
          'fanstatic.libraries': [
              'remote_wsgi = uvc.concierge.resources:library',
          ],
          'paste.app_factory': [
              'proxy = uvc.concierge:make_proxy',
          ],
          'paste.filter_app_factory': [
              'cipher = uvc.concierge.ticket:cipher',
          ],
      },
      )
