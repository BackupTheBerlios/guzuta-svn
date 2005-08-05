#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim: set foldmethod=marker:

import posix, sys
import libpypac

if __name__ == '__main__':
  uid = posix.getuid()
  if uid != 0:
    print 'not root bailing'
    sys.exit(1)
  (conf_list, server_list, noupgrade_list, ignore_list) = libpypac.read_conf()

  #server = '[community]'
  #ret = libpypac.sync(conf_list, server)
  #print ret
  #print conf_list

  for server in server_list:
    host = libpypac.sync(conf_list, server)
    if host == None:
      print 'failed'
    elif host == '0':
      print 'already updated'
    else:
      print host + '.'
