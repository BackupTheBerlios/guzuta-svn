#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim: set foldmethod=marker:


import libpypac.libpypac_0 as libpypac_0 
import libpypac.libpypac_1 as libpypac_1
import libpypac.libpypac_2 as libpypac_2
import libpypac.libpypac_3 as libpypac_3

server_dict, repo_list, noupgrade_list, ignore_list, hold_list = libpypac_0.read_conf()

# informacao acerca de um pacote:
# [[nome, versao, descricao, url, packager, build_date,
# install_date, size, reason], deps, required_by, filelist
#print libpypac_1.loc_pack_info_name('gtkpacman')
# total installed size
# returns size in bytes
#print libpypac_1.loc_size()
# optimize packagedatabase
#libpypac_1.opt_packdb()
# list local packages
# pkg_list, '/var/lib/pacman/local'
def xpto():
  pkg_list, t = libpypac_1.local_packages()

  print len(pkg_list)
  for pkg in pkg_list:
    #print pkg
    # [[nome, versao, descricao, url, packager, build_date,
    # install_date, size, reason], deps, required_by, filelist
    (pkg_info, deps, requires, filelist) = libpypac_1.loc_pack_info(pkg)
    #print pkg_info
    retcode, repo, pkg, cache, size = libpypac_2.exist_check(pkg_info[0], repo_list)
    #print pkg, repo
# search for server package info
# [[name, version, description, size], [dependencies]]
#print libpypac_1.serv_pack_info('abuse', repo_list)

# buggy
#print libpypac_1.pack_info('abuse', 'extra')
# packages not installed
# [[pkg_list], [repos_of_pkgs]]
#print libpypac_1.list_not_installed(repo_list)

# check for group
# [pkgs]
#print libpypac_1.check_group('kde', repo_list)

# check if a package belongs to a group
# Buggy
#print libpypac_1.check_pack_group('kdeedu', repo_list)

# check if package exists in the server
# [exists, repo, fullname, exists_in_cache, size]
#print libpypac_2.exist_check('abuse', repo_list)

# checks for dependencies
# providers, dependencies, errors, conflicts, size
#print libpypac_2.dep_install(['gtkpacman'], repo_list)

# checks for package when installing from file
# isto e para q??
#print libpypac_2.install_file_check(\
#  '/var/cache/pacman/pkg/kernel26-2.6.12.2-1.pkg.tar.gz')

# update check
# package_list, update_list, dep_list, err_list, conflict_list, orphan_list,
# size
#print libpypac_2.update_check(repo_list, ignore_list)

import profile, pstats

#profile.run('xpto()', 'ggg')
#p = pstats.Stats('ggg')
#p.sort_stats('calls', 'cum').print_stats()
xpto()
