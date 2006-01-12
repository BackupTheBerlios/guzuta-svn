#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim:set fdm=marker:

import os, os.path, sys, posix, signal, re, threading
import urllib, ftplib, httplib, shutil
from subprocess import *
import alpm
from optparse import OptionParser

# def trans_cb_ev(event, package1, package2): {{{
def trans_cb_ev(event, package1, package2):
  if event == alpm.PM_TRANS_EVT_CHECKDEPS_START:
    print 'checking dependencies...'
  elif event == alpm.PM_TRANS_EVT_FILECONFLICTS_START:
    print 'checking for file conflicts...'
  elif event == alpm.PM_TRANS_EVT_RESOLVEDEPS_START:
    print 'resolving dependencies...'
  elif event == alpm.PM_TRANS_EVT_INTERCONFLICTS_START:
    print 'looking for inter-conflicts...'
  elif event == alpm.PM_TRANS_EVT_FILECONFLICTS_START:
    print 'checking for file conflicts...'
  elif event == alpm.PM_TRANS_EVT_CHECKDEPS_DONE:
    print 'done.'
  elif event == alpm.PM_TRANS_EVT_FILECONFLICTS_DONE:
    print 'done.'
  elif event == alpm.PM_TRANS_EVT_RESOLVEDEPS_DONE:
    print 'done.'
  elif event == alpm.PM_TRANS_EVT_INTERCONFLICTS_DONE:
    print 'done.'
  elif event == alpm.PM_TRANS_EVT_ADD_START:
    print 'installing %s...' % package1.get_name()
  elif event == alpm.PM_TRANS_EVT_ADD_DONE:
    print 'done.'
  elif event == alpm.PM_TRANS_EVT_REMOVE_START:
    print 'removing %s...' % package1.get_name()
  elif event == alpm.PM_TRANS_EVT_REMOVE_DONE:
    print 'done.'
  elif event == alpm.PM_TRANS_EVT_UPGRADE_START:
    print 'upgrading %s...' % package1.get_name()
  elif event == alpm.PM_TRANS_EVT_UPGRADE_DONE:
    print 'done.'
  #print "Event:", (event, package, package2)
# }}}

# def trans_cb_conv(question, lpkg, spkg, treename): {{{
def trans_cb_conv(question, lpkg, spkg, treename):
  print "Question:", (question, lpkg, spkg, treename)

  if (question == alpm.PM_TRANS_CONV_INSTALL_IGNOREPKG):
    print "PM_TRANS_CONV_INSTALL_IGNOREPKG"
  if (question == alpm.PM_TRANS_CONV_REPLACE_PKG):
    print "PM_TRANS_CONV_REPLACE_PKG"
  if (question == alpm.PM_TRANS_CONV_LOCAL_NEWER):
    print "PM_TRANS_CONV_LOCAL_NEWER"
  if (question == alpm.PM_TRANS_CONV_LOCAL_UPTODATE):
    print "PM_TRANS_CONV_LOCAL_UPTODATE"
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

#class pacman: {{{
class pacman:
  """runs pacman. specify args for arguments passed, pacman_location for the
  location and pipeit to pipe the input/output streams. all arguments have a
  default value."""

  # def __init__(self, args = None, pacman_location = '/usr/bin/pacman', {{{
  def __init__(self, args = None, pacman_location = '/usr/bin/pacman',
      pipeit = None):
    self.args = args
    self.executable = pacman_location
    self.pipeit = pipeit
    self.readpipe = None
    self.writepipe = None
    self.errpipe = None
    self.pid = 0
  # }}}

  # def set_pipeit(self, pipeit): {{{
  def set_pipeit(self, pipeit):
    """changes modus operandi to pipe the stdin, stdout and stderr of pacman to
    pipes"""
    self.pipeit = pipeit
  # }}}

  # def get_pipeit(self): {{{
  def get_pipeit(self):
    """gets the current modus operandi"""
    return self.pipeit
  # }}}

  # def get_pid(self): {{{
  def get_pid(self):
    """gets pacman's pid, useful for os.waitpid"""
    return self.pid
  # }}}

  # def set_args(self, args): {{{
  def set_args(self, args):
    """sets pacman's arguments"""
    self.args = args
  # }}}

  # def set_executable(self, executable): {{{
  def set_executable(self, executable):
    """sets the pacman executable location. this is not likely to move..."""
    self.executable = executable
  # }}}

  # def get_read_pipe(self): {{{
  def get_read_pipe(self):
    """returns pacman's stout stream, piped"""
    return self.readpipe
  # }}}

  # def get_write_pipe(self): {{{
  def get_write_pipe(self):
    """returns pacman's stdin stream, piped"""
    return self.writepipe
  # }}}
  
  # def get_err_pipe(self): {{{
  def get_err_pipe(self):
    """returns pacman's stderror stream, piped. currently not used."""
    return self.errpipe
  # }}}

  # def run(self): {{{
  def run(self):
    """Runs pacman with the specified args"""

    cmd = self.executable + ' ' + self.args

    if self.pipeit == None:
      process = Popen([cmd], bufsize=0, shell=True, stdin=None,
          stdout=None, stderr=None, close_fds=True)
    else:
      process = Popen([cmd], bufsize=0, shell=True, stdin=PIPE,
          stdout=PIPE, stderr=PIPE, close_fds=True)
      self.pid = process.pid
      self.readpipe = process.stdout
      self.writepipe = process.stdin
      self.errpipe = process.stderr
    
    #self.shell.pid = process.pid

    #(self.shell.pid, self.shell.exit_status) = os.wait()
  # }}}
# }}}

# class shell: {{{
class shell:
  """this class implements some user friendly and front end friendly operations
  upon class pacman. if interactive is False, then it displays a prompt with
  some user commands available. if not it works suitably for use with a front
  end, like guzuta's gui ;)"""

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

  # def __init_alpm__(self): {{{
  def __init_alpm__(self):
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
    PACCACHE = "var/cache/pacman"
    
    try:
      config["CONFIGFILE"]
    except KeyError:
      config["CONFIGFILE"] = PACCONF
    
    config["DEBUG"] = alpm.PM_LOG_WARNING | alpm.PM_LOG_DEBUG |\
      alpm.PM_LOG_FLOW2 |alpm.PM_LOG_ERROR | alpm.PM_LOG_FLOW1 |\
      alpm.PM_LOG_FUNCTION

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

  # def __open_dbs__(self): {{{
  def __open_dbs__(self):
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

  # def __init__(self, command_line, lock, interactive = False): {{{
  def __init__(self, command_line, lock, interactive = False):
    #self.pacman = pacman(self)
    self.pacman = pacman()
    self.yesno = False

    self.trans = None
    tuple = self.__init_alpm__()
    if tuple == None:
      sys.exit(1)

    (self.alpm, self.pmc_syncs, self.config) = tuple

    self.__open_dbs__()

    self.lock = lock
    self.timer = threading.Timer(1.0, self.handle_timer)
    
    if interactive == True:
      self.pacman.set_pipeit(True)
    
    self.uid = posix.getuid()
    # pid of pacman process
    self.pid = 0
    
    # catch SIGINT and call the handler
    signal.signal(signal.SIGINT, self.sigint)
    
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
      os.kill(self.pacman.get_pid(), signal.SIGTERM)
      #print 'THREAD: pacman killed, exiting!'
      sys.exit(1)
  # }}}

    # commands and their description {{{
    self.commands = {
        'update': self.update,
        'upd' : self.update,
        'updatedb': self.updatedb,
        'updatepkgs': self.updatepkgs,
        'search': self.search,
        's': self.search,
        'localsearch': self.local_search,
        'ls': self.local_search,
        'repofiles': self.repofiles,
        'rf': self.repofiles,
        'install': self.install,
        'localinfo': self.local_info,
        'li': self.local_info,
        'info': self.info,
        'interactive': self.interactive,
        'remove': self.remove,
        'help': self.help,
        'quit': self.quit,
        'q': self.quit,
        'version': self.version
        }
    
    self.comm_description = {
        'update': 'update your system',
        'upd' : 'same as \'update\'',
        'updatedb': 'update pacman\'s repositories databases',
        'updatepkgs': 'update packages based on the updated databases',
        'search': 'search repositories',
        's': 'same as \'search\'',
        'localsearch': 'search locally installed packages',
        'ls' : 'same as \'localsearch\'',
        'repofiles': 'List all files in specified repositories',
        'rf': 'same as \'repofiles\'',
        'install' : 'install a package, must have root priviledges',
        'localinfo': 'display information about a package',
        'li': 'same as \'localinfo\'',
        'info': 'display server\'s information about a package',
        'remove' : 'remove a package, must have root priviledges',
        'help' : 'this text',
        'quit' : 'quit pycman',
        'q' : 'same as \'quit\'',
        'version': 'version'
    }
    # }}}

  # def get_prev_return(self): {{{
  def get_prev_return(self):
    return self.prev_return
  # }}}

  # def get_exit_status(self): {{{
  def get_exit_status(self):
    return self.exit_status
  # }}}
  
  # def sigint(self, signum, frame): {{{
  def sigint(self, signum, frame):
    # print 'Signal handler called with signal', signum
    # send SIGINT to pacman
    os.kill(self.pid, signum)
  # }}}

  # def sigkill(self): {{{
  def sigkill(self):
    os.kill(self.pid, signal.SIGKILL)
  # }}}

  # def interactive(self, what = ''): {{{
  def interactive(self, what = ''):
    if what == 'False':
      self.pacman.set_pipeit(False)
    else:
      self.pacman.set_pipeit(True)
    #print self.pacman.get_pipeit()
  # }}}

  # def get_yesno(self): {{{
  def get_yesno(self):
    return self.yesno
  # }}}

  # def send_to_pacman(self, what): {{{
  def send_to_pacman(self, what):
    self.pacman.get_write_pipe().write(what + '\n') # confirm
  # }}}
       
  # def check(self, big_list): {{{
  def check(self, big_list):
    i = 0

    for thing in big_list:
      #print 'thing is <%s>' % thing
      if i % 4 == 0:
        if thing != 'local':
          return False
      i = i + 1
    return True
  # }}}

  # def update(self): {{{
  def update(self):
    print 'Updating repositories\' databases...'
    self.updatedb()
    print 'Updating packages...'
    self.updatepkgs()
    return None
  # }}}

  # def updatepkgs(self, what = ''): {{{
  def updatepkgs(self, what = ''):
    ret = self.run_pacman_with('-Su')
    (self.pid, self.exit_status) = os.wait()
    return ret
  # }}}

  # def updatedb(self, what = ''): {{{
  def updatedb(self, what = ''):
    self.prev_return = None
    ret = self.run_pacman_with('-Sy')
    if self.pacman.get_pipeit() == True:
      ret = self.pacman.get_read_pipe().read()
      ret_err = self.pacman.get_err_pipe().read()
      
      (self.pid, self.exit_status) = os.wait()

      #for s in ret_err:
      #  print 's = <%s>' %s
      #print ret,ret_err
      #return ret, ret_err
      self.prev_return = ret, ret_err
    else:
      (self.pid, self.exit_status) = os.wait()
      #return None
      self.prev_return = None
  # }}}

  # def install_fresh_updates(self): {{{
  def install_fresh_updates(self):
    self.prev_return = None
    ret = self.run_pacman_with('-Su --noconfirm')

    (self.pid, self.exit_status) = os.wait()
    #return ret
    self.prev_return = ret
  # }}}

  # def get_fresh_updates_part_1(self): {{{
  def get_fresh_updates_part_1(self):
    self.prev_return = None
    ret = self.run_pacman_with('-Su')
   
    err = ''
    if self.pacman.get_pipeit() == True:
      (self.yesno, out) = self.__read_and_check_for_yesno__()
      self.exit_status = self.get_exit_status()
      if self.exit_status != 0:
        err = self.__capture_stderr__()
    else:
      (self.pid, self.exit_status) = os.wait()

    self.prev_return = (self.yesno, out, err)
  # }}}

  # def get_fresh_updates_part_2(self, pacman_upgrade, out, {{{
  # resolve_conflicts = 'do_nothing', pkg_not_to_upgrade = ''):
  def get_fresh_updates_part_2(self, pacman_upgrade, out,
      resolve_conflicts = 'do_nothing', pkg_not_to_upgrade = ''):
    self.prev_return = None
    # list of (pkg_name, version)
    updates = []

    out2 = ''
    if self.yesno:
      if resolve_conflicts == 'install':
        self.send_to_pacman('Y')
        (self.yesno, out2) = self.__read_and_check_for_yesno__()
        self.send_to_pacman('n')
      elif resolve_conflicts == 'do_nothing':
        self.send_to_pacman('n')
        err = self.__capture_stderr__()
        self.prev_return = self.get_exit_status(), err
        return
      else:
        self.send_to_pacman('n')

    if pacman_upgrade:
      (self.yesno, out2) = self.__read_and_check_for_yesno__()
      self.send_to_pacman('n')
    (self.pid, self.exit_status) = os.wait()

    pattern = '\n'
    if out2 != '':
      out = out2
    results = re.split(pattern, out)

    for result in results:
      if result.startswith('::'):
        continue
      if result.startswith('Remove'):
        continue
      if result.startswith('Total Package Size'):
        break
      print 'result: ', result
      if result != '':
        pattern2 = '\s'
        results2 = re.split(pattern2, result)

        for result2 in results2[1:]:
          if result2:
            first_dash = result2.index('-')
            last_dash = result2.rindex('-')
            before_last_dash = result2[:last_dash].rindex('-')

            name = result2[:before_last_dash]
            version = result2[before_last_dash+1:last_dash]

            if pkg_not_to_upgrade != '':
              if name != pkg_not_to_upgrade:
                updates.append(name)
            else:
              updates.append(name)

    ret_err = self.pacman.get_err_pipe().read()
    #return updates
    self.prev_return = updates
  # }}}
  
  # def get_fresh_updates(self): {{{
  def get_fresh_updates(self):
    self.prev_return = None
    ret = self.run_pacman_with('-Su')
    
    # list of (pkg_name, version)
    updates = []

    if self.pacman.get_pipeit() == True:
      (self.yesno, out) = self.__read_and_check_for_yesno__()

      if out.index('Upgrade pacman first?'):
        self.send_to_pacman('n')
        (self.pid, self.exit_status) = os.wait()
        self.prev_return = True
        return

      if self.yesno:
      #if self.pid != 0:
        self.send_to_pacman('n')
      (self.pid, self.exit_status) = os.wait()

      pattern = '\n'
      results = re.split(pattern, out)

      for result in results:
        if result.startswith('Total Package Size'):
          break
        if result != '':
          pattern2 = '\s'
          results2 = re.split(pattern2, result)

          for result2 in results2[1:]:
            if result2:
              first_dash = result2.index('-')
              last_dash = result2.rindex('-')
              before_last_dash = result2[:last_dash].rindex('-')

              name = result2[:before_last_dash]
              version = result2[before_last_dash+1:last_dash]

              updates.append(name)

      ret_err = self.pacman.get_err_pipe().read()
      #return updates
      self.prev_return = updates
    else:
      (self.pid, self.exit_status) = os.wait()

  # }}}

  # def __compile_pkg_dict_2__(self, pacman_output): {{{
  def __compile_pkg_dict_2__(self, pacman_output):
    pattern = '\n'
    pattern2 = '/|\s'

    results = re.split(pattern, pacman_output)

    all = {}
    pkgs = {}

    i = 0
    name = repo = version = description = ''
    buf = ''
    for r in results: # for every line
      if r != '':
        if r[0] != ' ': # if anything but description
          if buf != '': # description of the pkg before
            pkgs[name] = (repo, version, description)
            try:
              all[repo].append((name, version, description))
            except KeyError:
              all[repo] = []
              all[repo].append((name, version, description))
            buf = ''
          results2 = re.split(pattern2, r) # split by / or \s
          temp = []
          # repo, name, version
          for r2 in results2: # for every result
            if i == 0:
              repo = r2.strip()
              i = i + 1
            elif i == 1:
              name = r2.strip()
              i = i + 1
            elif i == 2:
              version = r2.strip()
              i = i + 1
        else: # starts with ' ', description
          i = 0
          if r != '':
            if buf == '':
              buf = r.strip()
            else:
              if buf[-1] == ' ':
                buf = buf + r.strip()
              else:
                buf = buf + ' ' + r.strip()
            description = buf

    if buf != '': # the very last description
      pkgs[name] = (repo, version, description)
      try:
        all[repo].append((name, version, description))
      except KeyError:
        all[repo] = []
        all[repo].append((name, version, description))
      buf = ''

    return (all, pkgs)
  # }}}

  # def __compile_pkg_dict__(self, pacman_output): {{{
  def __compile_pkg_dict__(self, pacman_output):
    # THIS WORKS {{{
    #all = []
    #buf = ''
    #for r in result:
    #  if r != '' and r[0] != ' ':
    #    if buf != '':
    #      all.append(buf)
    #      buf = ''
    #    result2 = re.split(pattern2, r)
    #    temp = []
    #    for r2 in result2:
    #      all.append(r2.strip())
    #  else: # starts with ' ', description
    #    if r != '':
    #      if buf == '':
    #        buf = r.strip()
    #      else:
    #        if buf[-1] == ' ':
    #          buf = buf + r.strip()
    #        else:
    #          buf = buf + ' ' + r.strip()

    #if buf != '':
    #  all.append(buf)
    #  buf = ''
    # }}}
    # new code 
    pattern = '\n'
    pattern2 = '/|\s'

    results = re.split(pattern, pacman_output)

    all = {}

    i = 0
    name = repo = version = description = ''
    buf = ''
    for r in results: # for every line
      if r != '' and r[0] != ' ': # if anything but description
        if buf != '': # description of the pkg before
          all[name] = (repo, version, description)
          buf = ''
        results2 = re.split(pattern2, r) # split by / or \s
        temp = []
        # repo, name, version
        for r2 in results2: # for every result
          if i == 0:
            repo = r2.strip()
            i = i + 1
          elif i == 1:
            name = r2.strip()
            i = i + 1
          elif i == 2:
            version = r2.strip()
            i = i + 1
      else: # starts with ' ', description
        i = 0
        if r != '':
          if buf == '':
            buf = r.strip()
          else:
            if buf[-1] == ' ':
              buf = buf + r.strip()
            else:
              buf = buf + ' ' + r.strip()
          description = buf

    if buf != '': # the very last description
      all[name] = (repo, version, description)
      buf = ''

    return all
  # }}}

  # def search(self, what = ''): {{{
  def search(self, what = ''):
    if what == '':
      self.run_pacman_with('-Ss \"\"')
    else:
      self.run_pacman_with('-Ss ' + what)

    if self.pacman.get_pipeit() == True:
      # get all pkgs which should have the format
      # reponame/name version

      list = self.pacman.get_read_pipe().read()

      all = self.__compile_pkg_dict__(list)

      (self.pid, self.exit_status) = os.wait()

      return all
    else:
      (self.pid, self.exit_status) = os.wait()
      return None
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

  # def local_search(self, what= ''): {{{
  def local_search(self, what= ''):
    self.prev_return = None
    if what == '':
      self.run_pacman_with('-Qs \"\"')
    else:
      self.run_pacman_with('-Qs ' + what)

    if self.pacman.get_pipeit() == True:
      # get all pkgs which should have the format
      # reponame/name version
    
      list = self.pacman.get_read_pipe().read()

      all = self.__compile_pkg_dict__(list)

      (self.pid, self.exit_status) = os.wait()
      #print self.check(all)
      #return all
      self.prev_return = all
      return
    else:
      (self.pid, self.exit_status) = os.wait()
      #return None
      self.prev_return = None
      return
  # }}}

  # def alpm_get_pmc_syncs(self): {{{
  def alpm_get_pmc_syncs(self):
    return self.pmc_syncs
  # }}}

  # def get_db_names(self): {{{
  def get_db_names(self):
    return self.db_names
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

  # def repofiles2(self): {{{
  def repofiles2(self):
    self.prev_return = None
    self.run_pacman_with('-Ss \"\"')

    self.alpm_repofiles2()

    if self.pacman.get_pipeit() == True:

      list = self.pacman.get_read_pipe().read()
      #(all, pkgs) = self.__compile_from_repo_list_dict_2__(list)
      (all, pkgs) = self.__compile_pkg_dict_2__(list)

      (self.pid, self.exit_status) = os.wait()
      #return (all, pkgs)
      self.prev_return = (all, pkgs)
      return
    else:
      (self.pid, self.exit_status) = os.wait()
      #return None
      self.prev_return = None
      return
  # }}}

  # def __compile_from_repo_list_dict__(self, pacman_output): {{{
  def __compile_from_repo_list_dict__(self, pacman_output):
    pattern = '\n' # split in lines
    results = re.split(pattern, pacman_output)
    
    pattern2 = '\s' # split with space

    all = {}
    
    # TODO: needed?
    pkgs = {}
    
    repo = name = version = ''
    i = 0
    # format: repo name version
 
    for r in results:
      results2 = re.split(pattern2, r)

      for r2 in results2:
        if i == 0:
          # repo
          repo = r2.strip()
          i = i + 1
        elif i == 1:
          # name
          name = r2.strip()
          i = i + 1
        else:
          # version, assemble all
          pkgs[name] = (repo, r2.strip())
          try:
            all[repo].append((name, r2.strip()))
          except KeyError:
            all[repo] = []
            all[repo].append((name, r2.strip()))
          i = 0
    return (all, pkgs)
  # }}}

  # def repofiles(self, what = ''): {{{
  def repofiles(self, what = ''):
    if what == '':
      self.run_pacman_with('-Sl')
    else:
      self.run_pacman_with('-Sl ' + what)

    if self.pacman.get_pipeit() == True:

      list = self.pacman.get_read_pipe().read()
      (all, pkgs) = self.__compile_from_repo_list_dict__(list)

      (self.pid, self.exit_status) = os.wait()
      return (all, pkgs)
    else:
      (self.pid, self.exit_status) = os.wait()
      return None
  # }}}

  # def __is_root__(self): {{{
  def __is_root__(self):
    uid = posix.getuid()
    return uid == 0
  # }}}

  # def __capture_stderr__(self): {{{
  def __capture_stderr__(self):
    line = 'a'
    out = ''

    stream = None

    if self.pacman.get_pipeit():
      stream = self.pacman.get_err_pipe()
    else:
      stream = sys.stderr

    while len(line) == 1:
      line = stream.read(1)
      out = out + line

    return out
  # }}}

  # def __capture_output__(self): {{{
  def __capture_output__(self):
    line = 'a'
    out = ''

    stream = None

    if self.pacman.get_pipeit():
      stream = self.pacman.get_read_pipe()
    else:
      stream = sys.stdout

    while len(line) == 1:
      line = stream.read(1)
      out = out + line

    return out
  # }}}

  # def __read_and_check_for_yesno__(self): {{{
  def __read_and_check_for_yesno__(self):
    line = 'a'
    out = ''

    while len(line) == 1: 
      line = self.pacman.get_read_pipe().read(1)
      #sys.stdout.write(line)
      out = out + line
      if line == '[':
        line2 = self.pacman.get_read_pipe().read(1)
        if line2 == 'Y':
          line3 = self.pacman.get_read_pipe().read(1)
          #sys.stdout.write(line2)
          out = out + line2
          if line3 == '/':
            line4 = self.pacman.get_read_pipe().read(1)
            #sys.stdout.write(line3)
            out = out + line3
            if line4 == 'n':
              line5 = self.pacman.get_read_pipe().read(1)
              #sys.stdout.write(line4)
              out = out + line4
              if line5 == ']':
                line6 = self.pacman.get_read_pipe().read(1)
                #sys.stdout.write(line5)
                out = out + line5
                if line6 == ' ':
                  #sys.stdout.write(line6)
                  out = out + line6
                  return (True, out)
    return (False, out)

  # }}}

  # def __is_already_installed__(self, what): {{{
  def __is_already_installed__(self, what):
    if not self.__is_root__():
      print "You are not ROOT. Bye bye."
      return
    
    (self.yesno, out) = self.__read_and_check_for_yesno__()
    
    regex = re.compile('is up to date|local version is newer')
    match = regex.search(out)

    if not match:
      return (False, out)
    elif match.span() != (0,0):
      return (True, out)
    #elif self.yesno:
    #  return (True, out)
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

  # def install_noconfirm(self, what = ''): {{{
  def install_noconfirm(self, what = ''):
    if not self.__is_root__():
      print "You are not ROOT. Bye bye."
      return
    if what == '':
      print 'Please specify a package to install'
      return

    self.run_pacman_with('-S ' + what + ' --noconfirm')

    os.wait()
  # }}}
  
  # def install_force_noconfirm(self, list): {{{
  def install_force_noconfirm(self, list):
    if not self.__is_root__():
      print "You are not ROOT. Bye bye."
      return

    what = ''

    for pkg_name in list:
      what = what + ' ' + pkg_name

    self.run_pacman_with('-Sf ' + what + ' --noconfirm')

    os.wait()
  # }}}
  
  # def remove_noconfirm(self, what = ''): {{{
  def remove_noconfirm(self, what = ''):
    if not self.__is_root__():
      print "You are not ROOT. Bye bye."
      return
    if what == '':
      print 'Please specify a package to remove'
      return

    self.run_pacman_with('-R ' + what + ' --noconfirm')

    os.wait()
  # }}}

  # def download_part_1(self, what = ''): {{{
  def download_part_1(self, what = ''):
    self.prev_return = None
    if not self.__is_root__():
      print "You are not ROOT. Bye bye."
      return
    if what == '':
      print 'Please specify a package to download'
      return

    self.run_pacman_with('-Sw ' + what)

    if self.pacman.get_pipeit():
      read_pipe = self.pacman.get_read_pipe()
      write_pipe = self.pacman.get_write_pipe()

      #read_pipe.flush()

      #if write_pipe != None:
      #   write_pipe.flush()
      #sys.stdout.flush()
      #sys.stdin.flush()
   
      #(found, output) = self.__is_already_installed__(what)
      
      (self.yesno, out) = self.__read_and_check_for_yesno__()

      self.pid = self.pacman.get_pid()

      #return (found, output)
      self.prev_return = out
      return
    else:
      #return (False, None)
      self.prev_return = None
      return
  # }}}
  
  # def download_part_2(self, txt_to_pacman): {{{
  def download_part_2(self, txt_to_pacman):
    self.prev_return = None
    self.send_to_pacman(txt_to_pacman)
    out = self.__capture_output__()

    self.prev_return = out
    return
  # }}}

  # def install_part_1(self, what = '', repo = ''): {{{
  def install_part_1(self, what = '', repo = ''):
    self.prev_return = None
    if not self.__is_root__():
      print "You are not ROOT. Bye bye."
      return
    if what == '':
      print 'Please specify a package to install'
      return

    if repo == '':
      self.run_pacman_with('-S ' + what)
    else:
      self.run_pacman_with('-S ' + repo + '/' + what)

    if self.pacman.get_pipeit():
      read_pipe = self.pacman.get_read_pipe()
      write_pipe = self.pacman.get_write_pipe()

      #read_pipe.flush()

      #if write_pipe != None:
      #   write_pipe.flush()
      #sys.stdout.flush()
      #sys.stdin.flush()
   
      (found, output) = self.__is_already_installed__(what)
      
      self.pid = self.pacman.get_pid()

      #return (found, output)
      self.prev_return = (found, output)
      return
    else:
      #return (False, None)
      self.prev_return = (False, None)
      return
  # }}}

  # def install_part_2(self, txt_to_pacman, wait = False): {{{
  def install_part_2(self, txt_to_pacman, wait = False):
    self.prev_return = None
    self.send_to_pacman(txt_to_pacman)
    # HACK
    (self.yesno, out) = self.__read_and_check_for_yesno__()

    if wait:
      (self.pid, self.exit_status) = os.wait()
    self.prev_return = (out, self.get_exit_status())
    return
  # }}}
  
  # def install_part_3(self, txt_to_pacman): {{{
  def install_part_3(self, txt_to_pacman): 
    self.prev_return = None
    self.send_to_pacman(txt_to_pacman)
    # HACK
    (self.yesno, out) = self.__read_and_check_for_yesno__()

    (self.pid, self.exit_status) = os.wait()
    
    #return (self.exit_status, (self.yesno, out))
    self.prev_return = (self.exit_status, (self.yesno, out))
    return
  # }}}

  # def install_part_2_no_wait(self, txt_to_pacman): {{{
  def install_part_2_no_wait(self, txt_to_pacman):
    self.prev_return = None
    self.send_to_pacman(txt_to_pacman)
    # HACK
    out = self.__read_and_check_for_yesno__()

    #return out
    self.prev_return = out
    return
  # }}}
  
  # def install(self, what = ''): {{{
  def install(self, what = ''):
    (ret, output) = self.install_part_1(what)

    if ret:
      # is already up to date, get confirmation from user about forcing the
      # install of the package
      print 'Package %s is already installed and up to date.' % what
      response = raw_input('Upgrade anyway? [Y/n] ')

      out = self.install_part_2(response)
      #print out,
      response = raw_input()
      (self.exit_status, (yesno, out)) = self.install_part_3(response)

      #if exit_status == 0:
      #  print out,
      
      return

    if self.yesno:
      # pacman is querying for user input
      #print output,

      response = raw_input()

      (self.exit_status, (yesno, out)) = self.install_part_3(response)
      #print out,

      return

    #OLD {{{
    #if not self.__is_root__():
    #  print "You are not ROOT. Bye bye."
    #  return
    #if what == '':
    #  print 'Please specify a package to install'
    #  return

    #self.run_pacman_with('-S ' + what)

    #if self.pacman.get_pipeit():
    #  read_pipe = self.pacman.get_read_pipe()
    #  write_pipe = self.pacman.get_write_pipe()

    #  read_pipe.flush()

    #  if write_pipe != None:
    #     write_pipe.flush()
    #  sys.stdout.flush()
    #  sys.stdin.flush()
   
    #  (found, output) = self.__is_already_installed__(what)

    #  if not found:
    #    #self.pacman.get_write_pipe().write('Y\n') # confirm
    #    os.wait()

    #    return True
    #  else:
    #    return False
    #else:
    #  os.wait()

    ## BACKUP {{{
    ##line = 'a'

    ##while len(line) == 1: 
    ##  line = self.pacman.get_read_pipe().read(1)
    ##  sys.stdout.write(line)
    ##  if line == '[':
    ##    line2 = self.pacman.get_read_pipe().read(1)
    ##    if line2 == 'Y':
    ##      line3 = self.pacman.get_read_pipe().read(1)
    ##      sys.stdout.write(line2)
    ##      if line3 == '/':
    ##        line4 = self.pacman.get_read_pipe().read(1)
    ##        sys.stdout.write(line3)
    ##        if line4 == 'n':
    ##          line5 = self.pacman.get_read_pipe().read(1)
    ##          sys.stdout.write(line4)
    ##          if line5 == ']':
    ##            line6 = self.pacman.get_read_pipe().read(1)
    ##            sys.stdout.write(line5)
    ##            if line6 == ' ':
    ##              sys.stdout.write(line6)
    ##              # [Y/n] !!!
    ##              if self.pacman.get_write_pipe != None:
    ##                self.pacman.get_write_pipe().write('Y\n')
    ##              else:
    ##                print 'write_pipe == None'
    ##  #else:
    ##    #sys.stdout.write(line)
    ## }}}
    #
    # }}}
  # }}}

  # def install_pkg_from_files(self, path_list): {{{
  def install_pkg_from_files(self, path_list):
    self.prev_return = None
    if path_list == [] or None:
      #return (None, None)
      self.prev_return = (None, None)
      return
    
    all_paths = ''

    for pathname in path_list:
      all_paths = all_paths + pathname + ' '
      
    self.run_pacman_with('-U ' + all_paths)
    
    (self.pid, self.exit_status) = os.wait()

    ret = self.pacman.get_read_pipe().read()
    ret_err = self.pacman.get_err_pipe().read()

    #return (ret, ret_err)
    self.prev_return = (ret, ret_err)
    return
  # }}}

  # def install_pkg_from_file(self, pathname): {{{
  def install_pkg_from_file(self, pathname):
    self.prev_return = None
    if pathname == '' or None:
      #return (None, None)
      self.prev_return = (None, None)
      return
    
    self.run_pacman_with('-U ' + pathname)
    
    (self.pid, self.exit_status) = os.wait()

    ret = self.pacman.get_read_pipe().read()
    ret_err = self.pacman.get_err_pipe().read()

    #return (ret, ret_err)
    self.prev_return = (ret, ret_err)
    return
  # }}}

  # def install_packages_noconfirm(self, pkg_list): {{{
  def install_packages_noconfirm(self, pkg_list):
    if not self.__is_root__():
      print "You are not ROOT. Bye bye."
      return
    
    what = ''
    for pkg_name in pkg_list:
      what = what + pkg_name + ' '
      
    self.run_pacman_with('-S ' + what + ' --noconfirm')

    (self.pid, self.exit_status) = os.wait()

    return self.exit_status
  # }}}
  
  # def __compile_pkg_info__(self, pacman_out): {{{
  def __compile_pkg_info__(self, pacman_output):
    pattern = '\n'

    all = []
    results = re.split(pattern, pacman_output)

    for r in results:
      if r.startswith('\t') or r.startswith(' '):
        all.append(r)
      else:
        all.append(r.strip())
      
    return all
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

  # def local_info(self, what = ''): {{{
  def local_info(self, what = ''):
    if what == '':
      print 'Please specify a package to query for info'
      return
    self.prev_return = None
    
    self.run_pacman_with('-Qi ' + what)
    
    if self.pacman.get_pipeit() == True:
      list = self.pacman.get_read_pipe().read()

      if list == '\n':
        (self.pid, self.exit_status) = os.wait()
        #return None
        self.prev_return = None
        return

      all = self.__compile_pkg_info__(list)

      (self.pid, self.exit_status) = os.wait()
      #return all
      self.prev_return = all
      return
    else:
      (self.pid, self.exit_status) = os.wait()
      #return None
      self.prev_return = None
      return
  # }}}
  
  # def alpm_info(self, what = ''): {{{
  def alpm_info(self, what = ''):
    (repo, version, desc) = self.pkgs[what]
    db = self.dbs_by_name[repo]
    try:
      pkg = db.read_pkg(what)
    except alpm.NoSuchPackageException:
      return None
    #return self.alpm_pkg_to_string(pkg)
    return self.alpm_remote_pkg_to_list(pkg)
  # }}}

  # def info(self, what = ''): {{{
  def info(self, what = ''):
    if what == '':
      print 'Please specify a package to query for info'
      return
    
    self.prev_return = None
    self.run_pacman_with('-Si ' + what)
    
    if self.pacman.get_pipeit() == True:
      list = self.pacman.get_read_pipe().read()

      all = self.__compile_pkg_info__(list)

      (self.pid, self.exit_status) = os.wait()
      if all == ['', '']:
        #return None
        self.prev_return = None
        return
      else:
        #return all
        self.prev_return = all
        return
    else:
      (self.pid, self.exit_status) = os.wait()
      #return None
      self.prev_return = None
      return
  # }}}
  
  #def remove_nodeps(self, what = ''): {{{
  def remove_nodeps(self, what = ''):
    uid = posix.getuid()
    if uid != 0:
      print "You are not ROOT. Bye bye."
      return
    if what == '':
      print 'Please specify a package to remove'
      return
    self.run_pacman_with('-Rd ' + what)
    
    out = self.__capture_output__()
    (pid, self.exit_status) = os.wait()
    if self.exit_status != 0:
      return False
    return True
  # }}}
  
  # def remove(self, what = ''): {{{
  def remove(self, what = ''):
    uid = posix.getuid()
    self.prev_return = None
    if uid != 0:
      print "You are not ROOT. Bye bye."
      return
    if what == '':
      print 'Please specify a package to remove'
      return
    self.run_pacman_with('-R ' + what)
    
    out = self.__capture_output__()
    (pid, self.exit_status) = os.wait()
    
    dependencies = []
    if self.exit_status != 0:
      pattern = '\n'
      tmp = re.split(pattern, out)
      for string in tmp:
        if string != '':
          dependencies.append(string[string.rfind(' ')+1:])
    #return (self.exit_status, dependencies, out)
    self.prev_return = (self.exit_status, dependencies, out)
    return
  # }}}
  
  # def get_pkg_files(self, what = ''): {{{
  def get_pkg_files(self, what = ''):
    uid = posix.getuid()
    self.prev_return = None
    #if uid != 0:
    #  print "You are not ROOT. Bye bye."
    #  return
    if what == '':
      print 'Please specify a package to remove'
      return
    
    self.run_pacman_with('-Ql ' + what)

    out = self.__capture_output__()
    (pid, self.exit_status) = os.wait()

    self.prev_return = (self.exit_status, out)
    return
  # }}}

  # def download(self, what = ''): {{{
  def download(self, what = ''):
    uid = posix.getuid()
    self.prev_return = None
    if uid != 0:
      print "You are not ROOT. Bye bye."
      return
    if what == '':
      print 'Please specify a package to remove'
      return
    print 'running <%s>' % ('-Sw ' + what)
    self.run_pacman_with('-Sw ' + what)

    #out = self.__capture_output__()
    (pid, self.exit_status) = os.wait()

    self.prev_return = (self.exit_status, out)
    return
  # }}}

  # help, quit, version {{{
  # def help(self, what = ''): {{{
  def help(self, what = ''):
    print 'Available commands:'
    for k,v in self.commands.iteritems():
      print k + ' - ' + self.comm_description[k]

  # }}}
  
  # def quit(self, what = ''): {{{
  def quit(self, what = ''):
    sys.exit(0)
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
  # }}}

  # def read_command(self): {{{
  def read_command(self):
    try:
      ret1 = raw_input(self.prompt)
      try:
        space_index = ret1.index(' ')
        rest = ret1[space_index + 1:]
      except ValueError:
        space_index = len(ret1)
        rest = ''
      command = ret1[0 : space_index] 
    except KeyboardInterrupt:
      print '\nInterrupted!'
      sys.exit(0)
    except EOFError:
      command = ''
      rest = ''
      #sys.exit(0)
      
    return command, rest
  # }}}

  # def go(self): {{{
  def go(self):
    print self.greet
    while(True):
      command, args = self.read_command()
      if command != '':
        if command in self.commands:
          ret = self.commands[command](args) 
          if ret != None:
            pass
        else:
          print 'Command \'' + command + '\' not found.'
      pacman_out = self.pacman.get_read_pipe()
      pacman_in = self.pacman.get_write_pipe()
  # }}}

  # def run_pacman_with(self, args): {{{
  def run_pacman_with(self, args):
    self.pacman.set_args(args)
    
    self.pacman.run()
    
    # KEEP THIS! {{{
    if self.pacman.get_pipeit() == True:
      self.pid = self.pacman.get_pid()
    #  
    #  read_pipe = self.pacman.get_read_pipe()
    #  write_pipe = self.pacman.get_write_pipe()

    #  read_pipe.flush()

    #  if write_pipe != None:
    #    write_pipe.flush()
    #  sys.stdout.flush()
    #  sys.stdin.flush()
    #  
    #  line = 'a'

    #  while len(line) == 1: 
    #    line = self.pacman.get_read_pipe().read(1)
    #    sys.stdout.write(line)
    #    if line == '[':
    #      line2 = self.pacman.get_read_pipe().read(1)
    #      if line2 == 'Y':
    #        line3 = self.pacman.get_read_pipe().read(1)
    #        sys.stdout.write(line2)
    #        if line3 == '/':
    #          line4 = self.pacman.get_read_pipe().read(1)
    #          sys.stdout.write(line3)
    #          if line4 == 'n':
    #            line5 = self.pacman.get_read_pipe().read(1)
    #            sys.stdout.write(line4)
    #            if line5 == ']':
    #              line6 = self.pacman.get_read_pipe().read(1)
    #              sys.stdout.write(line5)
    #              if line6 == ' ':
    #                sys.stdout.write(line6)
    #                # [Y/n] !!!
    #                if self.pacman.get_write_pipe != None:
    #                  self.pacman.get_write_pipe().write('Y\n')
    #                else:
    #                  print 'write_pipe == None'
    #      else:
    #        sys.stdout.write(line)
    #        
    #  t = os.waitpid(self.pid, os.WNOHANG)
    #  while t == (0, 0):
    #    t = os.waitpid(self.pid, os.WNOHANG)
    #else:
    #  (self.pid, self.exit_status) = os.wait()
    # }}}
  # }}}
  
  # def get_read_pipe(self): {{{
  def get_read_pipe(self):
    return self.pacman.get_read_pipe()
  # }}}

  # def get_err_pipe(self): {{{
  def get_err_pipe(self):
    return self.pacman.get_err_pipe()
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
        #print 'refreshing database: ', treename
        (filename, headers) = urllib.urlretrieve(url, destination)
        #print (filename, headers)
        if filename:
          # sync alpm
          #print 'sync\'ing ', treename
          try:
            print db.update(destination)
          except alpm.DatabaseException, instance:
            print inst
            return None
          try:
            os.remove(destination)
          except OSError:
            print '%s is a directory?' % destination
            return None
          break
  # }}}

  # def __alpm_download_package__(self, package_name): {{{
  def __alpm_download_package__(self, package_name):
    dest = '/tmp/'
  # }}}

  # def alpm_check_if_pkg_in_pkg_list(self, pkg_name, syncpkg_list): {{{
  def alpm_check_if_pkg_in_pkg_list(self, pkg_name, syncpkg_list):
    for syncpkg in syncpkg_list:
      if syncpkg.get_package().get_name() == pkg_name:
        return True
    return False
  # }}}

  # def alpm_transaction_init(self): {{{
  def alpm_transaction_init(self):
    self.trans = self.alpm.transaction_init(alpm.PM_TRANS_TYPE_SYNC, 0, trans_cb_ev)
  # }}}

  # def alpm_update_databases(self): {{{
  def alpm_update_databases(self):
    # PRE: alpm_transaction_init
    # POS: alpm_trans_release
    root = self.alpm.get_root()
    dbpath = self.alpm.get_db_path()
    upgrades = []
    missed_deps = []
    packages = []

    try:
      self.trans.sysupgrade()
      upgrades = self.trans.get_syncpackages()
      missed_deps = self.trans.prepare()
    except alpm.TransactionException, inst:
      print inst

    return (upgrades, missed_deps)
  # }}}

  # def alpm_transaction_release(self): {{{
  def alpm_transaction_release(self):
    self.trans.release()
  # }}}

  # def alpm_transaction_add_target(self, pkg_name): {{{
  def alpm_transaction_add_target(self, pkg_name):
    self.trans.add_target(pkg_name)
  # }}}

  # def alpm_transaction_prepare(self): {{{
  def alpm_transaction_prepare(self):
    return self.trans.prepare()
  # }}}
# }}}

# main {{{
if __name__ == '__main__':
  s = shell(sys.argv[1:], True)
  #s = shell(sys.argv[1:], False)
  #s = shell(sys.argv[1:], False, False)
  s.go()
# }}}

