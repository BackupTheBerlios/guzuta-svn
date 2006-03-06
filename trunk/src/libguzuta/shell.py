#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim:set fdm=marker:

# imports {{{
import os, os.path, sys, posix, signal, re, threading
import urllib, ftplib, httplib, shutil, time
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
          
          #for pmc in pmc_syncs:
          #  print "treename: <%s> section: <%s>" % (pmc["treename"], section)
          #  if pmc["treename"] == section:
          #    found = True
          #    sync = pmc
          #    break
          #print "VOU PROCURAR POR: ", section.upper()
          (found, sync_temp) = self.__find_pmc__(pmc_syncs, section)

          if not found:
            # start a new sync record
            #print "starting a new sync record"
            sync["treename"] = section
            sync["servers"] = []
            #print "pmc_syncs antes: ", pmc_syncs
            pmc_syncs.append(sync)
            sync = {}
            #print "pmc_syncs depois: ", pmc_syncs
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

    #for pmc in pmc_syncs:
    #  print "PMC: ", pmc
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
    #self.pacman = pacman(self)
    #self.pacman = pacman()
    self.yesno = False

    self.trans = None
    tuple = self.__init_alpm__(debug)
    if tuple == None:
      sys.exit(1)

    (self.alpm, self.pmc_syncs, self.config) = tuple

    self.__alpm_open_dbs__()

    self.lock = lock

    self.th_ended_event = threading.Event()

    self.timer = threading.Timer(1.0, self.handle_timer)
    
    #if interactive == True:
    #  self.pacman.set_pipeit(True)
    
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

    #self.timer.start()
    
    #self.opt_names = 'h:j:k:'
    #self.long_opt_names = ''

    #self.opts , self.long_opts = getopt.getopt(command_line, self.opt_names,
    #    self.long_opt_names)
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
    #self.db_names.append('local')
  # }}}

  # def __alpm_close_dbs__(self): {{{
  def __alpm_close_dbs__(self):
    #self.dbs_by_name = {}
    #self.db_names = []

    for sync in self.pmc_syncs:
      try:
        sync["db"].unregister()
        #del dbs_by_name[sync["treename"]]
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
    #return self.alpm.get_pkg_cache()
    return self.dbs_by_name[treename].get_package_iterator()
  # }}}
  
  # def alpm_repofiles2(self): {{{
  def alpm_repofiles2(self):
    # all[repo].append((name, version, description))
    # pkgs[name] = (repo, version, description)
    self.all = {}
    self.pkgs = {}

    for dbname, db in self.dbs_by_name.iteritems():
      if dbname != "local":
        self.all[dbname] = []

        for pkg in db.get_package_iterator():
          name = pkg.get_name()
          version = pkg.get_version()
          description = pkg.get_description()

          self.all[dbname].append((name, version, description))
          self.pkgs[name] = (dbname, version, description)
    return (self.all, self.pkgs)
  # }}}

  # def alpm_get_pmc_syncs(self): {{{
  def alpm_get_pmc_syncs(self):
    return self.pmc_syncs
  # }}}

  # def alpm_local_search(self, what = ''): {{{
  def alpm_local_search(self, what = ''):
    self.local_pkgs = {}

    #for dbname, db in self.dbs_by_name.iteritems():
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
    #return self.alpm_pkg_to_string(pkg)
    return self.alpm_pkg_to_list(pkg)
  # }}}

  # def alpm_info(self, what = ''): {{{
  def alpm_info(self, what = ''):
    (repo, version, desc) = self.pkgs[what]
    db = self.dbs_by_name[repo]

    try:
      #pkg = db.read_pkg(what)
      pkg_cache_list = db.get_pkg_cache()

      for pkg_c in pkg_cache_list:
        if pkg_c.get_name() == what:
          pkg = pkg_c
          break
    except alpm.NoSuchPackageException:
      return None
    #return self.alpm_pkg_to_string(pkg)
    return self.alpm_remote_pkg_to_list(pkg)
  # }}}

  # def alpm_download_file(self, url, destination): {{{
  def alpm_download_file(self, url, destination):
    try:
      (filename, headers) = urllib.urlretrieve(url, destination)
    except IOError:
      filename = None

    return filename
  # }}}

  # def alpm_refresh_dbs(self): {{{
  def alpm_refresh_dbs(self):
    for pmc in self.pmc_syncs:
      treename = pmc['treename']
      db = pmc['db']
      gzfile = treename + '.db.tar.gz'
      destination = '/tmp/' + gzfile
      servers = pmc['servers']
      for server in servers:
        url = server['protocol'] + '://' + server['server'] + server['path'] +\
          gzfile
        #(filename, headers) = urllib.urlretrieve(url, destination)
        filename = self.alpm_download_file(url, destination)
        if filename:
          # sync alpm
          try:
            print db.update(destination)
          except alpm.DatabaseException, instance:
            print instance
            return None
          try:
            os.remove(destination)
          except OSError:
            print '%s is a directory?' % destination
            return None
          break
  # }}}

  # def alpm_get_package_files(self, pkg_name): {{{
  def alpm_get_package_files(self, pkg_name):
    db_name = self.alpm_get_pkg_dbname(pkg_name)

    db = self.dbs_by_name['local']

    try:
      pkg = db.read_pkg(pkg_name)
    except alpm.NoSuchPackageException:
      return None

    return pkg.get_files()
  # }}}

  # def alpm_get_pkg_dbname(self, pkg_name): {{{
  def alpm_get_pkg_dbname(self, pkg_name):
    return self.pkgs[pkg_name][0]
  # }}}

  # def alpm_get_pkg_version(self, pkg_name): {{{
  def alpm_get_pkg_version(self, pkg_name):
    return self.pkgs[pkg_name][1]
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

  # def alpm_download_packages(self, files, progress_bar): {{{
  def alpm_download_packages(self, files, progress_bar):
    print 'DOWNLOADING: ', files
    self.prev_return = None
    ret = []
    
    #for pkg_name in pkg_names:
    for path in files:
      print 'PATH: ', path
    #for sync,path in zip(sync_packages, files):
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

      filename = self.alpm_download_package(pkg_name, pkg_ver,
          db_name, path)

      if filename != None:
        ret.append(filename)
        str = '%s/%s-%s downloaded.' %\
            (db_name, pkg_name, pkg_ver)
        #gtk.gdk.threads_enter()
        progress_bar.set_text(str)
        time.sleep(1)
        #progress_bar.pulse()
        #gtk.gdk.threads_leave()
      else:
        self.prev_return = None
        self.th_ended_event.set()
        return
    self.prev_return = ret
    self.th_ended_event.set()
    return
  # }}}

  # def alpm_download_package(self, package_name, version, dbname, path): {{{
  def alpm_download_package(self, package_name, version, dbname, path):
    #self.all[dbname].append((name, version, description))
    #self.pkgs[name] = (dbname, version, description)

    #dbname = self.pkgs[package_name][0]
    #dbname = self.alpm_get_pkg_dbname(package_name)
    #version = self.pkgs[package_name][1]
    #version = self.alpm_get_pkg_version(package_name)
    
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

      #destination = self.config['ROOT'] + self.config['CACHEDIR'] + '/pkg/'\
      #    + package_name + '-' + version + '.pkg.tar.gz'

      destination = path

      url = server_record['protocol'] + '://' + server_record['server']\
          + server_record['path'] + package_name + '-' + version + '.pkg.tar.gz'

      filename = self.alpm_download_file(url, destination)

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

  # def alpm_update_databases(self): {{{
  def alpm_update_databases(self):
    root = self.alpm.get_root()
    dbpath = self.alpm.get_db_path()
    upgrades = []
    missed_deps = []
    packages = []

    #self.alpm_transaction_init()
    self.alpm_transaction_init(alpm.PM_TRANS_TYPE_SYNC, 0, trans_cb_ev,\
        trans_cb_conv)

    try:
      self.trans.sysupgrade()
      upgrades = self.trans.get_syncpackages()
      missed_deps = self.trans.prepare()
    except alpm.TransactionException, inst:
      print inst

    self.alpm_transaction_release()
    
    return (upgrades, missed_deps)
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
    self.trans.prepare()
    self.th_ended_event.set()
  # }}}

  # def alpm_transaction_commit(self): {{{
  def alpm_transaction_commit(self):
    self.trans.commit()
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
      #return (None, None)
      self.prev_return = (None, None)
      return
    
    self.alpm_transaction_init(alpm.PM_TRANS_TYPE_UPGRADE,\
        alpm.PM_TRANS_FLAG_RECURSE, trans_cb_ev, trans_cb_conv)

    for path in path_list:
      self.alpm_transaction_add_target(path)

    try:
      self.alpm_transaction_prepare()
    #except alpm.UnsatisfiedDependenciesTransactionException, depmiss_list:
    #  raise
    #except alpm.ConflictingDependenciesTransactionException, conflict_list:
    #  raise
    #except alpm.ConflictingFilesTransactionException, conflict_list:
    #  raise
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

