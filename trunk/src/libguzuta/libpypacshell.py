#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim: set foldmethod=marker:

import libpypac

# class libpypacshell: {{{
class libpypacshell:
  # def __init__(): {{{
  def __init__(self):
    self.conf_list, self.server_list, self.noupgrade_list, self.ignore_list =\
        libpypac.read_conf()
    #self.test()
  # }}}

  # def test(self): {{{
  def test(self):
    #print 'conf_list: ', self.conf_list
    #print 'server_list: ', self.server_list
    #print 'noupgrade_list: ', self.noupgrade_list
    #print 'ignore_list: ', self.ignore_list

    print '====== exist_check ================'
    print libpypac.exist_check('bash', self.server_list)
    print '====== check_group ================'
    print libpypac.check_group('gnome', self.server_list)
    print '====== check_pack_group ==========='
    print libpypac.check_pack_group('metacity', self.server_list)
    print '====== check_update ==============='
    print libpypac.check_update(self.server_list, self.ignore_list)
    print '====== dep_single ================='
    # print libpypac.dep_install('abcde', self.server_list) # BUG?
    print libpypac.dep_single('kernel26', self.server_list)
    # print libpypac.desc_search('cdparanoia', self.server_list) # ???
    print '====== get_loc_pack ==============='
    print libpypac.get_loc_pack('bash')
    print '====== get_local_package =========='
    print libpypac.get_local_package('bash')
    print '====== list_locals ================'
    print libpypac.list_locals()
    print '====== list_not_installed ========='
    print libpypac.list_not_installed(self.server_list) # FSCK!
    print '====== loc_pack_info =============='
    print libpypac.loc_pack_info('bash')
    print '====== loc_size ==================='
    print libpypac.loc_size()
    #print libpypac.old_check('bash') # not needed I guess
    print '====== orphans ===================='
    print libpypac.orphans()
    #print libpypac.print_cache()
    print '====== provide_check =============='
    print libpypac.provide_check('bmp-cvs', self.server_list)
    print '====== provide_check_local ========'
    print libpypac.provide_check_local('bmp-cvs')
    print '====== require_check =============='
    print libpypac.require_check('glibc')
    print '====== search_group ==============='
    print libpypac.search_group('gnome', self.server_list)
    print '====== search ====================='
    print libpypac.search('bash', self.server_list)
  # }}}
  
  # def info(self, what = ''): {{{
  def info(self, what = ''):
    #self.test()
    info = libpypac.pack_info(what, self.server_list)
    print 'info: ', info
    return info
  # }}}

  # def local_search(self, what= ''): {{{
  def local_search(self, what= ''):
    ret = libpypac.search(what, self.server_list)
    print 'ret: ', ret
  # }}}
# }}}

# main {{{
if __name__ == '__main__':
  c = libpypacshell()
  c.info('abcm2ps')
  c.local_search('abcm2ps')
# }}}

