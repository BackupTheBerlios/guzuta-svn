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
    self.test()

  def test(self):
    #print 'conf_list: ', self.conf_list
    #print 'server_list: ', self.server_list
    #print 'noupgrade_list: ', self.noupgrade_list
    #print 'ignore_list: ', self.ignore_list

    print libpypac.exist_check('bash', self.server_list)
    print libpypac.check_group('gnome', self.server_list)
    print libpypac.check_pack_group('metacity', self.server_list)
    print libpypac.check_update(self.server_list, self.ignore_list)
    # print libpypac.dep_install('abcde', self.server_list) # BUG?
    print libpypac.dep_single('kernel26', self.server_list)
    # print libpypac.desc_search('cdparanoia', self.server_list) # ???
    print libpypac.get_loc_pack('bash')
    print libpypac.get_local_package('bash')
    print libpypac.list_locals()
    print libpypac.list_not_installed(self.server_list) # FSCK!
    print libpypac.loc_pack_info('bash')
    print libpypac.loc_size()
    #print libpypac.old_check('bash') # not needed I guess
    print libpypac.orphans()
    #print libpypac.print_cache()
    print libpypac.provide_check('bmp-cvs', self.server_list)
    print libpypac.provide_check_local('bmp-cvs')
    print libpypac.require_check('glibc')
    print libpypac.search_group('gnome', self.server_list)
    print libpypac.search('bash', self.server_list)
  # }}}
# }}}

# main {{{
if __name__ == '__main__':
  c = libpypacshell()
# }}}
