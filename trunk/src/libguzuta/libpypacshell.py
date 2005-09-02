#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim: set foldmethod=marker:

#import libpypac

import libpypac_devel.libpypac_0 as libpypac_0 
import libpypac_devel.libpypac_1 as libpypac_1
import libpypac_devel.libpypac_2 as libpypac_2
import libpypac_devel.libpypac_3 as libpypac_3
import libpypac_devel.libpypac_misc as libpypac_misc

# class libpypacshell: {{{
class libpypacshell:
  # def __init__(): {{{
  def __init__(self):
    self.conf_list, self.server_list, self.noupgrade_list, self.ignore_list =\
        libpypac_0.read_conf()
    #self.test()
  # }}}

  # def test(self): {{{
  def test(self):
    #print 'conf_list: ', self.conf_list
    #print 'server_list: ', self.server_list
    #print 'noupgrade_list: ', self.noupgrade_list
    #print 'ignore_list: ', self.ignore_list

    print '====== exist_check ================'
    print libpypac_2.exist_check('bash', self.server_list)
    print '====== check_group ================'
    print libpypac_1.check_group('gnome', self.server_list)
    print '====== check_pack_group ==========='
    print libpypac_1.check_pack_group('metacity', self.server_list)
    print '====== check_update ==============='
    #print libpypac_devel.check_update(self.server_list, self.ignore_list)
    print '====== dep_single ================='
    print libpypac_2.dep_install('abcde', self.server_list) # BUG?
    #print libpypac_devel.dep_single('kernel26', self.server_list)
    print '====== desc_search ================'
    print libpypac_1.search_desc('cdparanoia', self.server_list) # ???
    print '====== get_loc_pack ==============='
    print libpypac_misc.get_loc_pack('bash')
    print '====== get_local_package =========='
    print libpypac_devel.get_local_package('bash')
    print '====== list_locals ================'
    print libpypac_devel.list_locals()
    print '====== list_not_installed ========='
    print libpypac_devel.list_not_installed(self.server_list) # FSCK!
    print '====== loc_pack_info =============='
    print libpypac_devel.loc_pack_info('bash')
    print '====== loc_size ==================='
    print libpypac_devel.loc_size()
    #print libpypac_devel.old_check('bash') # not needed I guess
    print '====== orphans ===================='
    print libpypac_devel.orphans()
    #print libpypac_devel.print_cache()
    print '====== provide_check =============='
    print libpypac_devel.provide_check('bmp-cvs', self.server_list)
    print '====== provide_check_local ========'
    print libpypac_devel.provide_check_local('bmp-cvs')
    print '====== require_check =============='
    print libpypac_devel.require_check('glibc')
    print '====== search_group ==============='
    print libpypac_devel.search_group('gnome', self.server_list)
    print '====== search ====================='
    print libpypac_devel.search('bash', self.server_list)
  # }}}
  
  # def info(self, what = ''): {{{
  def info(self, what = ''):
    #self.test()
    info = libpypac_devel.pack_info(what, self.server_list)
    print 'info: ', info
    return info
  # }}}

  # def local_search(self, what= ''): {{{
  def local_search(self, what= ''):
    ret = libpypac_devel.search(what, self.server_list)
    print 'ret: ', ret
  # }}}
# }}}

# main {{{
if __name__ == '__main__':
  c = libpypacshell()
  c.info('abcm2ps')
  c.local_search('abcm2ps')
# }}}

