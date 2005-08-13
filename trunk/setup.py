#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim: set foldmethod=marker:

from distutils.core import setup

setup(name='guzuta',
    version='0.0.1',
    package_dir={'guzuta': 'Guzuta'},
    packages=['guzuta'],
    data_files=[
                ('/usr/share/guzuta', ['guzuta2.glade']),
                ('/usr/bin', ['guzuta'])
      ]
    )
