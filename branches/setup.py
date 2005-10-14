#!/usr/bin/env python

from distutils.core import setup

setup(name='guzuta',
      version='0.0.1',
      package_dir={'': 'src'},
      packages=['libguzuta'],
      data_files=[('/usr/share/guzuta/', ['data/guzuta3.glade']),
                  ('/usr/share/guzuta/', ['data/guzuta_icon_transparent.png']),
                  ('/opt/gnome/share/applications/', ['data/guzuta.desktop']),
                  ('/opt/kde/share/applications/kde/', ['data/guzuta.desktop']),
		  ('/usr/share/applications/', ['data/guzuta.desktop']),
                  ('/usr/bin', ['src/guzuta'])],
      )
