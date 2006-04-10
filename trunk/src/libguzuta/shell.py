#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim:set fdm=marker:

# imports {{{
import os, os.path, sys, posix, signal, re, threading
import urllib, ftplib, httplib, urllib2, shutil, time
from subprocess import *
import alpm
from optparse import OptionParser
import pygtk
pygtk.require('2.0')
import gtk
import gtk.gdk
if gtk.pygtk_version < (2,3,90):
  raise SystemExit
import gobject
import threading
# }}}

# def trans_cb_ev(event, package1, package2): {{{
def trans_cb_ev(event, package1, package2):
  if event == alpm.PM_TRANS_EVT_CHECKDEPS_START:
    print '[checking dependencies...]'
  elif event == alpm.PM_TRANS_EVT_FILECONFLICTS_START:
    print '[checking for file conflicts...]'
  elif event == alpm.PM_TRANS_EVT_RESOLVEDEPS_START:
    print '[resolving dependencies...]'
  elif event == alpm.PM_TRANS_EVT_INTERCONFLICTS_START:
    print '[looking for inter-conflicts...]'
  elif event == alpm.PM_TRANS_EVT_FILECONFLICTS_START:
    print '[checking for file conflicts...]'
  elif event == alpm.PM_TRANS_EVT_CHECKDEPS_DONE:
    print '[done.]'
  elif event == alpm.PM_TRANS_EVT_FILECONFLICTS_DONE:
    print '[done.]'
  elif event == alpm.PM_TRANS_EVT_RESOLVEDEPS_DONE:
    print '[done.]'
  elif event == alpm.PM_TRANS_EVT_INTERCONFLICTS_DONE:
    print '[done.]'
  elif event == alpm.PM_TRANS_EVT_ADD_START:
    print '[installing %s...' % package1.get_name()
  elif event == alpm.PM_TRANS_EVT_ADD_DONE:
    print '[done.]'
  elif event == alpm.PM_TRANS_EVT_REMOVE_START:
    print '[removing %s...' % package1.get_name()
  elif event == alpm.PM_TRANS_EVT_REMOVE_DONE:
    print '[done.]'
  elif event == alpm.PM_TRANS_EVT_UPGRADE_START:
    print '[upgrading %s...' % package1.get_name()
  elif event == alpm.PM_TRANS_EVT_UPGRADE_DONE:
    print '[done.]'
  #print "Event:", (event, package, package2)
# }}}

# def trans_cb_conv(question, lpkg, spkg, treename): {{{
def trans_cb_conv(question, lpkg, spkg, treename):
  print '[Question:', (question, lpkg, spkg, treename), ']'

  if (question == alpm.PM_TRANS_CONV_INSTALL_IGNOREPKG):
    print "[PM_TRANS_CONV_INSTALL_IGNOREPKG]"
  if (question == alpm.PM_TRANS_CONV_REPLACE_PKG):
    print "[PM_TRANS_CONV_REPLACE_PKG]"
  if (question == alpm.PM_TRANS_CONV_LOCAL_NEWER):
    print "[PM_TRANS_CONV_LOCAL_NEWER]"
  if (question == alpm.PM_TRANS_CONV_LOCAL_UPTODATE):
    print "[PM_TRANS_CONV_LOCAL_UPTODATE]"
  return 4
# }}}

# def f(level, message): {{{
def f(level, message):
  level_str = ''
  if level == alpm.PM_LOG_DEBUG:
    level_str = 'DEBUG'
  elif level == alpm.PM_LOG_ERROR:
    level_str = 'ERROR'
  elif level == alpm.PM_LOG_WARNING:
    level_str = 'WARNING'
  elif level == alpm.PM_LOG_FLOW1:
    level_str = 'FLOW1'
  elif level == alpm.PM_LOG_FLOW2:
    level_str = 'FLOW2'
  elif level == alpm.PM_LOG_FUNCTION:
    level_str = 'FUNCTION'
  else:
    level_str = 'UNKNOWN'

  print '%s: %s' % (level_str, message)
# }}}

# class shell: {{{
class shell:
  # def __find_pmc__(self, pmc_syncs, treename): {{{
  def __find_pmc__(self, pmc_syncs, treename):
    for pmc in pmc_syncs:
      if pmc["treename"] == treename:
        return (True, pmc)
    return (False, None)
  # }}}

  # def __parseconfig__(self, alpm, file, pmc_syncs, config): {{{
  def __parseconfig__(self, alpm, file, pmc_syncs, config):
    linenum = 0
    conf_file = open(file)
    lines = conf_file.readlines()
    sync = {}

    for line in lines:
      linenum = linenum + 1
      line = line[:-1]
      line = line.strip()
      
      if len(line) == 0 or line[0] == '#':
        continue

      if (line[0] == '[' and line[len(line)-1] == ']'):
        # new config section
        section = line[1:len(line)-1]
        if len(section) == 0:
          print "config: line %d: bad section name" % linenum
          return 1

        if section == "local":
          print "config: line %d: '%s' is reserved and cannot be used as a\
          package tree" % (linenum, section)
          return 1

        if section != "options":
          found = False
          
          (found, sync_temp) = self.__find_pmc__(pmc_syncs, section)

          if not found:
            sync["treename"] = section
            sync["servers"] = []
            pmc_syncs.append(sync)
            sync = {}
          else:
            sync = sync_temp

      else:
        # directive
        l = line.split('=')
        key = l[0]
        other = l[1]

        if not key:
          print "config: line %d: syntax error" % linenum
          return 1
        key = key[:-1]
        key = key.strip()
        key = key.upper()
        other = other[1:]
        if not len(section) and key != "INCLUDE":
          print "config: line %d: all directives must belong to a section" %\
          linenum
          return 1
        if not other:
          if key == "NOPASSIVEFTP":
            config["NOPASSIVEFTP"] = True
          elif key == "USESYSLOG":
            alpm.set_use_syslog(True)
          elif key == "ILOVECANDY":
            config["CHOMP"] = True
          else:
            print "config: line %d: syntax error" % linenum
        else: # there's more
          other = other.strip()

          if key == "INCLUDE":
            conf = other
            self.__parseconfig__(alpm, conf, pmc_syncs, config)
          elif section == "options":
            if key  == "NOUPGRADE":
              pkgs = other.split(' ')
              for noup_pkg in pkgs:
                alpm.set_no_upgrade(noup_pkg)
            elif key == "NOEXTRACT":
              pkgs = other.split(' ')
              for noextract_pkg in pkgs:
                alpm.set_no_extract(noextract_pkg)
            elif key == "IGNOREPKG":
              pkgs = other.split(' ')
              for ignore_pkg in pkgs:
                alpm.set_ignore_pkg(ignore_pkg)
            elif key == "HOLDPKG":
              pkgs = other.split(' ')
              for hold_pkg in pkgs:
                alpm.set_hold_pkg(hold_pkg)
            elif key == "DBPATH":
              if other[0] == '/':
                other = other[1:]
              config["DBPATH"] = other
            elif key == "CACHEDIR":
              if other[0] == '/':
                other = other[1:]
              config["CACHEDIR"] = other
            elif key == "LOGFILE":
              alpm.set_log_file(other)
            elif key == "XFERCOMMAND":
              config["XFERCOMMAND"] = other
            elif key == "PROXYSERVER":
              l = other.split("://")
              this = l[0]
              other2 = l[1]

              if other2:
                other2 = other2[3:]

                if not other2:
                  print "config: line %d: bad server location" % linenum
              config["proxyhost"] = other2
            elif key == "PROXYPORT":
              config["proxyport"] = int(other)
            else:
              print "config: line %d: syntax error" % linenum
          else:
            if key == "SERVER":
              
              (found, sync_temp) = self.__find_pmc__(pmc_syncs, section)
              if found:
                sync = sync_temp

              server = {}
              server["server"] = ""
              server["path"] = ""
              server["protocol"] = ""

              l = other.split("://")
              protocol = l[0]
              location = l[1]

              if not protocol:
                print "config: line %d: bad server protocol" % linenum
                return 1

              if not location:
                print "config: line %d: bad server location" % linenum
                return 1

              server["protocol"] = protocol
              if protocol == "ftp" or protocol == "http":
                # split the url into domain and path
                slash_pos = location.index("/")
                left = location[:slash_pos]
                right = location[slash_pos:]

                if not slash_pos:
                  # no path included, default to /
                  server["path"] = "/"
                else:
                  # add a trailing slash if we need to
                  if right[len(right)-1] == "/":
                    server["path"] = right
                  else:
                    server["path"] = ("%s/" % right)
                  server["server"] = left
              elif protocol == "file":
                # add a trailing slash if we need to
                slash_pos = location.index("/")
                left = location[:slash_pos]
                right = location[slash_pos:]

                if right[len(right)-1] == '/':
                  server["path"] = right
                else:
                  server["path"] = ("%s/" % right)
              else:
                print "config: line %d: procotol %s is not supported" %\
                  (linenum, ptr)
              # add to the list
              try:
                sync["servers"].append(server)
              except KeyError:
                sync["servers"] = []
                sync["servers"].append(server)
            else:
              print "config: line %d: syntax error" % linenum

  # }}}

  # def __init_alpm__(self, debug): {{{
  def __init_alpm__(self, debug):
    pmc_syncs = []
    config = {}

    PACROOT = "/"

    try:
      if config["ROOT"][len(config["ROOT"])] != "/":
        config["ROOT"] = ("%s/" % config["ROOT"])
    except KeyError:
      config["ROOT"] = "/"
    try:
      a = alpm.Alpm(config["ROOT"])
    except RuntimeError, inst:
      print inst
      return None

    PACCONF = "/etc/pacman.conf"
    PACDB = "var/lib/pacman"
    PACCACHE = "var/cache/pacman/pkg"
    
    try:
      config["CONFIGFILE"]
    except KeyError:
      config["CONFIGFILE"] = PACCONF
    
    #config["DEBUG"] = alpm.PM_LOG_WARNING | alpm.PM_LOG_DEBUG |\
    #  alpm.PM_LOG_FLOW2 |alpm.PM_LOG_ERROR | alpm.PM_LOG_FLOW1 |\
    #  alpm.PM_LOG_FUNCTION
    config["DEBUG"] = debug

    self.__parseconfig__(a, config["CONFIGFILE"], pmc_syncs, config)

    try:
      config["DBPATH"]
    except KeyError:
      config["DBPATH"] = PACDB

    try:
      config["CACHE"]
    except KeyError:
      config["CACHE"] = PACCACHE

    a.set_log_mask(config["DEBUG"])
    a.set_log_callback(f)
    a.set_db_path(config["DBPATH"])
    a.set_cache_dir(config["CACHE"])

    try:
      config["DBPATH"]
    except KeyError:
      config["DBPATH"] = PACDB

    return (a, pmc_syncs, config)
  # }}}

  # def __init__(self, command_line, lock, debug, interactive = False): {{{
  def __init__(self, command_line, lock, debug, interactive = False):
    self.yesno = False
    self.last_exception = None

    self.trans = None
    tuple = self.__init_alpm__(debug)
    if tuple == None:
      sys.exit(1)

    (self.alpm, self.pmc_syncs, self.config) = tuple

    self.__alpm_open_dbs__()

    self.lock = lock

    self.th_ended_event = threading.Event()
    self.th_ended_event.clear()

    self.timer = threading.Timer(1.0, self.handle_timer)
    
    self.uid = posix.getuid()
    # pid of pacman process
    self.pid = 0
    
    # catch SIGINT and call the handler
    #signal.signal(signal.SIGINT, self.sigint)
    
    self.PS1 = "#"
    self.greet = "Welcome to guzuta!\n" 
    self.prompt = self.PS1 + " "

    self.prev_return = None
    self.REASON_EXPLICIT = 0

  # }}}

  # def release(self): {{{
  def release(self):
    self.alpm.release()
  # }}}

  # def start_timer(self): {{{
  def start_timer(self):
    self.timer = threading.Timer(1.0, self.handle_timer)
    self.timer.start()
  # }}}

  # def handle_timer(self): {{{
  def handle_timer(self):
    #print 'THREAD: in handle_timer...'
    if self.lock.acquire(False):
      # lock successful, loop
      self.lock.release()
      self.timer = threading.Timer(1.0, self.handle_timer)
      #print 'THREAD: timer looping'
      self.timer.start()
    else:
      # lock unsuccessful, bail out
      #print 'THREAD: killing pacman...'
      #os.kill(self.pacman.get_pid(), signal.SIGKILL)
      #os.kill(self.pacman.get_pid(), signal.SIGTERM)
      #print 'THREAD: pacman killed, exiting!'
      sys.exit(1)
  # }}}

  # def get_prev_return(self): {{{
  def get_prev_return(self):
    return self.prev_return
  # }}}

  # def get_db_names(self): {{{
  def get_db_names(self):
    return self.db_names
  # }}}

  # def __is_root__(self): {{{
  def __is_root__(self):
    uid = posix.getuid()
    return uid == 0
  # }}}

  # def version(self): {{{
  def version(self):
    print 'Guzuta %s' % version
    print 'Copyright (C) 2005 Joao Estevao <trankas@gmail.com>'
    print ''
    print '''This program may be freely redistributed under
the terms of the GNU General Public License'''
    print ''
  # }}}

  # alpm-ified {{{
  # def __alpm_open_dbs__(self): {{{
  def __alpm_open_dbs__(self):
    self.dbs_by_name = {}
    self.db_names = []

    for sync in self.pmc_syncs:
      try:
        sync["db"] = self.alpm.register_db(sync["treename"])
        self.dbs_by_name[sync["treename"]] = sync["db"]
        self.db_names.append(sync["treename"])
      except RuntimeError:
        print "could not register ", sync["treename"]
        sys.exit(1)
    self.dbs_by_name["local"] = self.alpm.register_db("local")
  # }}}

  # def __alpm_close_dbs__(self): {{{
  def __alpm_close_dbs__(self):
    for sync in self.pmc_syncs:
      try:
        sync["db"].unregister()
      except KeyError:
        pass
    self.dbs_by_name["local"].unregister()
  # }}}

  # def alpm_get_dbs(self): {{{
  def alpm_get_dbs(self):
    return self.dbs
  # }}}

  # def alpm_get_dbs_by_name(self): {{{
  def alpm_get_dbs_by_name(self):
    return self.dbs_by_name
  # }}}

  # def alpm_get_package_cache(self, treename): {{{
  def alpm_get_package_cache(self, treename):
    return self.dbs_by_name[treename].get_pkg_cache()
  # }}}

  # def alpm_get_package_iterator(self, treename): {{{
  def alpm_get_package_iterator(self, treename):
    return self.dbs_by_name[treename].get_package_iterator()
  # }}}
  
  # def alpm_repofiles2(self): {{{
  def alpm_repofiles2(self):
    self.all = {}
    self.pkgs = {}
    self.groups = {}
    self.groups_by_repo = {}

    for dbname, db in self.dbs_by_name.iteritems():
      if dbname != "local":
        self.all[dbname] = []
        self.groups_by_repo[dbname] = []

        # get packages
        try:
          iter = db.get_package_iterator()
        except RuntimeError, inst:
          raise RuntimeError, inst

        for pkg in db.get_package_iterator():
          name = pkg.get_name()
          version = pkg.get_version()
          description = pkg.get_description()

          self.all[dbname].append((name, version, description))
          if name not in self.pkgs:
            self.pkgs[name] = {}
          self.pkgs[name][dbname] = (dbname, version, description)

        # get groups
        try:
          for grp in db.get_group_iterator():
            grp_name = grp.get_name()
            grp_pkgs = grp.get_package_names()

            self.groups_by_repo[dbname].append((grp_name, grp_pkgs))
            self.groups[grp_name] = (dbname, grp_pkgs)
        except alpm.NoGroupsFoundException:
          # no groups found
          pass


      else: # 'local'
        for pkg in db.get_package_iterator():
          name = pkg.get_name()
          version = pkg.get_version()
          description = pkg.get_description()

          if name not in self.pkgs:
            self.pkgs[name] = {}
          self.pkgs[name]['local'] = ('local', version, description)
    return (self.all, self.pkgs, self.groups, self.groups_by_repo)
  # }}}

  # def alpm_get_pmc_syncs(self): {{{
  def alpm_get_pmc_syncs(self):
    return self.pmc_syncs
  # }}}

  # def alpm_get_groups(self, db_name): {{{
  def alpm_get_groups(self, db_name):
    self.local_groups = {}

    db = self.dbs_by_name[db_name]
    try:
      for grp in db.get_group_iterator():
        name = grp.get_name()
        package_names = grp.get_package_names()
        self.local_groups[name] = package_names
    except alpm.NoGroupsFoundException:
      return {}
    return self.local_groups
  # }}}

  # def alpm_local_search(self, what = ''): {{{
  def alpm_local_search(self, what = ''):
    self.local_pkgs = {}

    dbname = 'local'
    db = self.dbs_by_name[dbname]
    for pkg in db.get_package_iterator():
      name = pkg.get_name()
      version = pkg.get_version()
      description = pkg.get_description()

      self.local_pkgs[name] = (dbname, version, description)

    return self.local_pkgs
  # }}}

  # def alpm_pkg_in_repo(self, pkgname, repo): {{{
  def alpm_pkg_in_repo(self, pkgname, repo):
    pkg_cache = self.dbs_by_name[repo].get_pkg_cache()

    for pkg in pkg_cache:
      if pkg.get_name() == pkgname:
        return (True, pkg.get_version())
    return (False, None)
  # }}}

  # def alpm_get_pkg_repo(self, pkgname): {{{
  def alpm_get_pkg_repo(self, pkgname):
    for repo in self.db_names:
      (found, version) = self.alpm_pkg_in_repo(pkgname, repo)
      if found:
        return (repo, version)
    return (None, '--')
  # }}}

  # def alpm_pkg_to_list(self, pkg): {{{
  def alpm_pkg_to_list(self, pkg):
    name = pkg.get_name()
    version = pkg.get_version()
    groups = pkg.get_groups()
    packager = pkg.get_packager()
    url = pkg.get_url()
    license = pkg.get_license()
    architecture = pkg.get_architecture()
    size = pkg.get_size()
    build_date = pkg.get_build_date()
    install_date = pkg.get_install_date()
    scriptlet = pkg.get_scriptlet()
    reason = pkg.get_reason()
    provides = pkg.get_provides()
    depends = pkg.get_depends()
    requires = pkg.get_requires()
    conflicts = pkg.get_conflicts()
    description = pkg.get_description()
    maxcols = 80
    cols = 0

    string = ''
    line = ''
    list = []
    list.append('Name\t: ' + name)
    list.append('Version\t: ' + version)
    string = string + 'Groups\t: '

    line = string
    if len(groups):
      for group in groups:
        if len(line) >= maxcols:
          line = group + ' '
          string = string + '\n\t\t\t\t' + group + ' '
        else:
          line = line + group + ' '
          string = string + group + ' '
    else:
      string = string + 'None'

    list.append(string)
    list.append('Packager\t: ' + packager)
    list.append('URL\t: ' + url)
    if license == None:
      license = 'None'
    list.append('License\t: ' + license)
    list.append('Architecture\t: ' + architecture)
    list.append('Size\t: ' + str(size))
    list.append('Build Date\t: ' + build_date)
    list.append('Install Date\t: ' + install_date)
    if scriptlet == 0:
      scriptlet = 'No'
    else:
      scriptlet = 'Yes'
    list.append('Install Script\t: ' + scriptlet)
    string = ''
    string = string + 'Reason\t: '
    if reason == 0:
      string = string + 'installed as a dependency for another package'
    else:
      string = string + 'explicitly installed'
    list.append(string)
    string = ''
    string = string + 'Provides\t: '

    line = string
    if len(provides):
      for provide in provides:
        if len(line) >= maxcols:
          line = provide + ' '
          string = string + '\n\t\t\t\t' + provide + ' '
        else:
          line = line + provide + ' '
          string = string + provide + ' '
    else:
      string = string + 'None'

    list.append(string)
    string = ''
    string = string + 'Depends On\t: '

    line = string
    if len(depends):
      for depend in depends:
        if len(line) >= maxcols:
          line = depend + ' '
          string = string + '\n\t\t\t\t' + depend + ' '
        else:
          line = line + depend + ' '
          string = string + depend + ' '
    else:
      string = string + 'None'
    
    list.append(string)
    string = ''
    string = string + 'Required By\t: '

    line = string
    if len(requires):
      for require in requires:
        if len(line) >= maxcols:
          line = require + ' '
          string = string + '\n\t\t\t\t' + require + ' '
        else:
          line = line + require + ' '
          string = string + require + ' '
    else:
      string = string + 'None'
    
    list.append(string)
    string = ''
    string = string + 'Conflicts With\t: '

    line = string
    if len(conflicts):
      for conflict in conflicts:
        if len(line) >= maxcols:
          line = conflict + ' '
          string = string + '\n\t\t\t\t' + conflict + ' '
        else:
          line = line + conflict + ' '
          string = string + conflict + ' '
    else:
      string = string + 'None'

    list.append(string)
    list.append('Description\t: ' + description)
    return list
  # }}}

  # def alpm_group_to_list(self, group): {{{
  def alpm_group_to_list(self, group):
    l = []
    s = ''
    l.append('Group:\t' + group.get_name())
    l.append('Packages:\t')
    for pkg_name in group.get_package_names():
      l.append('\t' + pkg_name)
    return l
  # }}}

  # def alpm_remote_pkg_to_list(self, pkg): {{{
  def alpm_remote_pkg_to_list(self, pkg):
    name = pkg.get_name()
    version = pkg.get_version()
    groups = pkg.get_groups()
    provides = pkg.get_provides()
    depends = pkg.get_depends()
    conflicts = pkg.get_conflicts()
    replaces = pkg.get_replaces()
    size = pkg.get_size()
    description = pkg.get_description()
    md5sum = pkg.get_md5sum()

    maxcols = 80
    cols = 0

    string = ''
    line = ''
    list = []
    list.append('Name\t: ' + name)
    list.append('Version\t: ' + version)
    string = string + 'Groups\t: '

    line = string
    if len(groups):
      for group in groups:
        if len(line) >= maxcols:
          line = group + ' '
          string = string + '\n\t\t\t\t' + group + ' '
        else:
          line = line + group + ' '
          string = string + group + ' '
    else:
      string = string + 'None'

    list.append(string)
    string = ''
    string = string + 'Provides\t: '

    line = string
    if len(provides):
      for provide in provides:
        if len(line) >= maxcols:
          line = provide + ' '
          string = string + '\n\t\t\t\t' + provide + ' '
        else:
          line = line + provide + ' '
          string = string + provide + ' '
    else:
      string = string + 'None'

    list.append(string)
    string = ''
    string = string + 'Depends On\t: '

    line = string
    if len(depends):
      for depend in depends:
        if len(line) >= maxcols:
          line = depend + ' '
          string = string + '\n\t\t\t\t' + depend + ' '
        else:
          line = line + depend + ' '
          string = string + depend + ' '
    else:
      string = string + 'None'
    
    list.append(string)
    string = ''
    string = string + 'Conflicts With\t: '

    line = string
    if len(conflicts):
      for conflict in conflicts:
        if len(line) >= maxcols:
          line = conflict + ' '
          string = string + '\n\t\t\t\t' + conflict + ' '
        else:
          line = line + conflict + ' '
          string = string + conflict + ' '
    else:
      string = string + 'None'

    string = ''
    string = string + 'Replaces\t: '

    line = string
    if len(replaces):
      for replace in replaces:
        if len(line) >= maxcols:
          line = replace + ' '
          string = string + '\n\t\t\t\t' + replace + ' '
        else:
          line = line + replace + ' '
          string = string + replace + ' '
    else:
      string = string + 'None'

    list.append(string)
    list.append('Size (compressed)\t: ' + str(size))
    list.append('Description\t: ' + description)
    return list
  # }}}

  # def alpm_pkg_to_string(self, pkg): {{{
  def alpm_pkg_to_string(self, pkg):
    name = pkg.get_name()
    version = pkg.get_version()
    groups = pkg.get_groups()
    packager = pkg.get_packager()
    url = pkg.get_url()
    license = pkg.get_license()
    architecture = pkg.get_architecture()
    size = pkg.get_size()
    build_date = pkg.get_build_date()
    install_date = pkg.get_install_date()
    scriptlet = pkg.get_scriptlet()
    reason = pkg.get_reason()
    provides = pkg.get_provides()
    depends = pkg.get_depends()
    requires = pkg.get_requires()
    conflicts = pkg.get_conflicts()
    description = pkg.get_description()

    string = ""
    string = string + 'Name\t: ' + name + '\n'
    string = string + 'Version\t: ' + version + '\n'
    string = string + 'Groups\t: '
    if len(groups):
      for group in groups:
        string = string + group + ' '
    else:
      string = string + 'None'
    string = string + '\nPackager\t: ' + packager + '\n'
    string = string + 'URL\t: ' + url + '\n'
    if license == None:
      license = 'None'
    string = string + 'License\t: ' + license + '\n'
    string = string + 'Architecture\t: ' + architecture + '\n'
    string = string + 'Size\t: ' + str(size) + '\n'
    string = string + 'Build Date\t: ' + build_date + '\n'
    string = string + 'Install Date\t: ' + install_date + '\n'
    if scriptlet == 0:
      scriptlet = 'No'
    else:
      scriptlet = 'Yes'
    string = string + 'Install Script\t: ' + scriptlet + '\n'
    string = string + 'Reason\t: '
    if reason == 0:
      string = string + 'installed as a dependency for another package'
    else:
      string = string + 'explicitly installed'
    string = string + 'Provides\t: '
    if len(provides):
      for provide in provides:
        string = string + provide + ' '
    else:
      string = string + 'None'
    string = string + '\n'
    string = string + 'Depends On\t: '
    if len(depends):
      for depend in depends:
        string = string + depend + ' '
    else:
      string = string + 'None'
    string = string + '\n'
    string = string + 'Required By\t: '
    if len(requires):
      for require in pkg.get_requires():
        string = string + require + ' '
    else:
      string = string + 'None'
    string = string + '\n'
    string = string + 'Conflicts With\t: '
    if len(conflicts):
      for conflict in pkg.get_conflicts():
        string = string + conflict + ' '
    else:
      string = string + 'None'
    string = string + '\n'
    string = string + 'Description\t: ' + pkg.get_description()
    return string
  # }}}

  # def alpm_local_info(self, what = ''): {{{
  def alpm_local_info(self, what = ''):
    db = self.dbs_by_name['local']
    try:
      pkg = db.read_pkg(what)
    except alpm.NoSuchPackageException:
      return None
    return self.alpm_pkg_to_list(pkg)
  # }}}

  # def alpm_group_local_info(self, what = ''): {{{
  def alpm_group_local_info(self, what = ''):
    db = self.dbs_by_name['local']
    try:
      grp = db.read_group(what)
    except alpm.NoSuchGroupException:
      return None

    return self.alpm_group_to_list(grp)
  # }}}

  # def alpm_info(self, what = '', repo_name = None): {{{
  def alpm_info(self, what = '', repo_name = None):
    if not repo_name:
      print self.pkgs[what]
      try:
        tuple = self.pkgs[what]['local']
      except KeyError:
        tuple = self.pkgs[what][self.pkgs[what].keys()[0]]
    else:
      if repo_name == 'not installed' or repo_name == 'installed' or\
          repo_name == 'all':
            tuple = self.pkgs[what][self.pkgs[what].keys()[0]]
      else:
        tuple = self.pkgs[what][repo_name]

    (repo, version, desc) = tuple
    db = self.dbs_by_name[repo]

    pkg = None
    try:
      pkg_cache_list = db.get_pkg_cache()

      for pkg_c in pkg_cache_list:
        if pkg_c.get_name() == what:
          pkg = pkg_c
          break
    except alpm.NoSuchPackageException:
      return None
    if pkg == None:
      return None
    else:
      return self.alpm_remote_pkg_to_list(pkg)
  # }}}

  # def alpm_group_info(self, what = ''): {{{
  def alpm_group_info(self, what = ''):
    grp = None

    l = []
    for dbname, db in self.dbs_by_name.iteritems():
      try:
        grp = db.read_group(what)
      except alpm.NoSuchGroupException:
        continue
      else:
        l = l + self.alpm_group_to_list(grp)
    return l
  # }}}

  # TODO: show kb/s if possible
  # def alpm_download_file(self, url, destination, report_hook = None): {{{
  def alpm_download_file(self, url, destination, report_hook = None):
    #time.sleep(2)
    try:
      is_db = True
      if not report_hook:
        (filename, headers) = urllib.urlretrieve(url, destination)
      else:
        print 'URL: ', url
        try:
          url.rindex('.db.tar.gz')
        except ValueError:
          is_db = False

        if is_db:
          self.retrieving = url[url.rindex("/")+1:url.rindex(".db.tar.gz")]
        else:
          self.retrieving = url[url.rindex("/")+1:]
        (filename, headers) = urllib.urlretrieve(url, destination, report_hook)
    except IOError:
      filename = None

    return filename
  # }}}

  # def alpm_get_package_files(self, pkg_name, repo_name = None): {{{
  def alpm_get_package_files(self, pkg_name, repo_name = None):
    if not repo_name:
      db_name = self.alpm_get_pkg_dbname(pkg_name, 'local')
    else:
      db_name = self.alpm_get_pkg_dbname(pkg_name, repo_name)

    db = self.dbs_by_name['local']

    try:
      pkg = db.read_pkg(pkg_name)
    except alpm.NoSuchPackageException:
      return None

    return pkg.get_files()
  # }}}

  # def alpm_get_pkg_dbname(self, pkg_name, repo_name): {{{
  def alpm_get_pkg_dbname(self, pkg_name, repo_name):
    try:
      self.pkgs[pkg_name][repo_name][0]
    except KeyError:
      return self.local_pkgs[pkg_name][0]
  # }}}

  # def alpm_get_pkg_version(self, pkg_name, repo_name): {{{
  def alpm_get_pkg_version(self, pkg_name, repo_name):
    return self.pkgs[pkg_name][repo_name][1]
  # }}}

  # def alpm_pkg_name_version_from_path(self, path): {{{
  def alpm_pkg_name_version_from_path(self, path):
    last_slash_pos = path.rindex('/')
    lastdash_pos = path.rindex('-')
    dashver_pos = path[: lastdash_pos].rindex('-')
    dotpkg_pos = path[: path[: path.rindex('.')].rindex('.')].rindex('.')

    pkg_name = path[last_slash_pos+1: dashver_pos]
    pkg_ver = path[dashver_pos+1: dotpkg_pos]

    return pkg_name, pkg_ver
  # }}}

  # def alpm_download_packages(self, files, progress_bar, report_hook = None): {{{
  def alpm_download_packages(self, files, progress_bar, report_hook = None):
    print 'DOWNLOADING: ', files
    self.prev_return = None
    ret = []
    
    for path in files:
      print 'PATH: ', path
      pkg_name, pkg_ver = self.alpm_pkg_name_version_from_path(path)

      db_name = ''
      for pmc in self.pmc_syncs:
        db = pmc['db']

        try:
          pkg = db.read_pkg(pkg_name)
          if pkg:
            db_name = db.get_tree_name()
        except alpm.NoSuchPackageException:
          pass

      self.alpm_download_package(pkg_name, pkg_ver,
          db_name, path, report_hook)

      filename = self.prev_return
      print 'Filename: ', filename
      if filename != None:
        ret.append(filename)
        str = '%s/%s-%s downloaded.' %\
            (db_name, pkg_name, pkg_ver)
        progress_bar.set_text(str)
      else:
        self.prev_return = None
        self.th_ended_event.set()
        return
    self.prev_return = ret
    self.th_ended_event.set()
    return
  # }}}

  # def alpm_download_package(self, package_name, version, dbname, path, {{{
  # report_hook = None):
  def alpm_download_package(self, package_name, version, dbname, path,
      report_hook = None):
    pmc = None
    for pmc_record in self.pmc_syncs:
      if pmc_record['treename'] == dbname:
        pmc = pmc_record
        break

    for server_record in pmc['servers']:
      try:
        self.config['CACHEDIR']
      except KeyError:
        self.config['CACHEDIR'] = 'var/cache/pacman'

      destination = path

      url = server_record['protocol'] + '://' + server_record['server']\
          + server_record['path'] + package_name + '-' + version + '.pkg.tar.gz'

      filename = self.alpm_download_file(url, destination, report_hook)

      print '%s downloaded to %s' % (package_name, filename)

      self.prev_return = filename
      return
  # }}}

  # def alpm_check_if_pkg_in_pkg_list(self, pkg_name, syncpkg_list): {{{
  def alpm_check_if_pkg_in_pkg_list(self, pkg_name, syncpkg_list):
    for syncpkg in syncpkg_list:
      if syncpkg.get_package().get_name() == pkg_name:
        return True
    return False
  # }}}

  # def alpm_transaction_init(self): {{{
  #def alpm_transaction_init(self):
  #  self.trans = self.alpm.transaction_init(alpm.PM_TRANS_TYPE_SYNC, 0, trans_cb_ev)
  # }}}

  # def alpm_transaction_init(self, type, flags, cb_event, cb_conversation): {{{
  def alpm_transaction_init(self, type, flags, cb_event, cb_conversation=None):
    if cb_conversation != None:
      self.trans = self.alpm.transaction_init(type, flags, cb_event,\
          cb_conversation)
    else:
      self.trans = self.alpm.transaction_init(type, flags, cb_event)
  # }}}

  # def alpm_refresh_dbs(self, report_hook = None): {{{
  def alpm_refresh_dbs(self, report_hook = None):
    for pmc in self.pmc_syncs:
      treename = pmc['treename']
      db = pmc['db']
      gzfile = treename + '.db.tar.gz'
      destination = '/tmp/' + gzfile
      servers = pmc['servers']
      for server in servers:
        url = server['protocol'] + '://' + server['server'] + server['path'] +\
          gzfile
        filename = self.alpm_download_file(url, destination, report_hook)
        if filename:
          # sync alpm
          try:
            print db.update(destination)
          except alpm.DatabaseException, instance:
            self.th_ended_event.set()
            raise alpm.DatabaseException, instance
          try:
            pass
          except OSError, instance:
            self.th_ended_event.set()
            raise OSError, instance
          break
    self.th_ended_event.set()
    return
  # }}}

  # def alpm_transaction_sysupgrade(self): {{{
  def alpm_transaction_sysupgrade(self):
    try:
      self.trans.sysupgrade()
    except Exception, inst:
      raise Exception, inst
  # }}}

  # def alpm_update_databases(self): {{{
  def alpm_update_databases(self):
    self.prev_return = None
    root = self.alpm.get_root()
    dbpath = self.alpm.get_db_path()
    upgrades = []
    missed_deps = []
    packages = []

    self.alpm_transaction_init(alpm.PM_TRANS_TYPE_SYNC, 0, trans_cb_ev,\
        trans_cb_conv)

    try:
      # TODO: run this in thread and display the busy_dialog &
      # busy_progress_bar3
      self.trans.sysupgrade()
      upgrades = self.trans.get_syncpackages()
      missed_deps = self.trans.prepare()
    except alpm.TransactionException, inst:
      self.last_exception = (1, inst)
      self.th_ended_event.set()
      #raise alpm.TransactionException, inst
    except alpm.UnsatisfiedDependenciesTransactionException, inst:
      self.last_exception = (2, inst)
      self.th_ended_event.set()
      #raise alpm.UnsatisfiedDependenciesTransactionException, inst

    self.prev_return = (upgrades, missed_deps)
    self.th_ended_event.set()
    return
  # }}}

  # def alpm_transaction_release(self): {{{
  def alpm_transaction_release(self):
    print 'TRANSACTION RELEASED'
    self.trans.release()
  # }}}

  # def alpm_transaction_add_target(self, pkg_name): {{{
  def alpm_transaction_add_target(self, pkg_name):
    try:
      self.trans.add_target(pkg_name)
    except alpm.DuplicateTargetTransactionException, inst:
      print inst, pkg_name
      return True
    except alpm.PackageNotFoundTransactionException, inst:
      print inst, pkg_name
      return False
    return True
  # }}}

  # def alpm_transaction_prepare(self): {{{
  def alpm_transaction_prepare(self):
    try:
      self.trans.prepare()
    except alpm.UnsatisfiedDependenciesTransactionException, inst:
      self.last_exception = (1, inst)
      self.th_ended_event.set()
    except alpm.ConflictingDependenciesTransactionException, inst:
      self.last_exception = (2, inst)
      self.th_ended_event.set()
    except RuntimeError, inst:
      self.last_exception = (3, inst)
      self.th_ended_event.set()
    except alpm.ConflictingFilesTransactionException, inst:
      self.last_exception = (4, inst)
      self.th_ended_event.set()
    self.th_ended_event.set()
  # }}}

  # def alpm_transaction_commit(self): {{{
  def alpm_transaction_commit(self):
    try:
      self.trans.commit()
    except alpm.ConflictingDependenciesTransactionException, inst:
      self.last_exception = (2, inst)
      self.th_ended_event
    except RuntimeError, inst:
      self.last_exception = (3, inst)
      self.th_ended_event
    except alpm.ConflictingFilesTransactionException, inst:
      self.last_exception = (4, inst)
      self.th_ended_event.set()
    self.th_ended_event.set()
  # }}}

  # def alpm_transaction_get_sync_packages(self): {{{
  def alpm_transaction_get_sync_packages(self):
    return self.trans.get_syncpackages()
  # }}}

  # def alpm_install_pkg_from_files(self, path_list): {{{
  def alpm_install_pkg_from_files(self, path_list):
    self.prev_return = None
    error = ''
    if path_list == [] or None:
      self.prev_return = (None, None)
      return
    
    self.alpm_transaction_init(alpm.PM_TRANS_TYPE_UPGRADE,\
        alpm.PM_TRANS_FLAG_RECURSE, trans_cb_ev, trans_cb_conv)

    for path in path_list:
      self.alpm_transaction_add_target(path)

    try:
      self.alpm_transaction_prepare()
    except Exception:
      raise

    self.alpm_transaction_release()

    # actually install the packages
    try:
      self.alpm_transaction_commit()
    except RuntimeError, inst:
      raise

    self.prev_return = None
    return
  # }}}

  # def alpm_get_alpm(self): {{{
  def alpm_get_alpm(self):
    return self.alpm
  # }}}
  # }}}
# }}}

# main {{{
if __name__ == '__main__':
  s = shell(sys.argv[1:], True)
  #s = shell(sys.argv[1:], False)
  #s = shell(sys.argv[1:], False, False)
  s.go()
# }}}

