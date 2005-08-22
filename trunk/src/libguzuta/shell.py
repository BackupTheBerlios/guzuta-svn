#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim: set foldmethod=marker:

import os, sys, posix, signal, re
from subprocess import *

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

  # def __init__(self, command_line, interactive = False): {{{
  def __init__(self, command_line, interactive = False):
    #self.pacman = pacman(self)
    self.pacman = pacman()
    self.yesno = False
    
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
    
    #self.opt_names = 'h:j:k:'
    #self.long_opt_names = ''

    #self.opts , self.long_opts = getopt.getopt(command_line, self.opt_names,
    #    self.long_opt_names)
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
    ret = self.run_pacman_with('-Sy')
    if self.pacman.get_pipeit() == True:
      ret = self.pacman.get_read_pipe().read()
      ret_err = self.pacman.get_err_pipe().read()
      
      (self.pid, self.exit_status) = os.wait()

      #for s in ret_err:
      #  print 's = <%s>' %s
      #print ret,ret_err
      return ret, ret_err
    else:
      (self.pid, self.exit_status) = os.wait()
      return None
  # }}}

  # def install_fresh_updates(self): {{{
  def install_fresh_updates(self):
    ret = self.run_pacman_with('-Su --noconfirm')

    (self.pid, self.exit_status) = os.wait()
    return ret
  # }}}

  # def get_fresh_updates(self): {{{
  def get_fresh_updates(self):
    ret = self.run_pacman_with('-Su')
    
    # list of (pkg_name, version)
    updates = []

    if self.pacman.get_pipeit() == True:
      (self.yesno, out) = self.__read_and_check_for_yesno__()

      if self.yesno:
      #if self.pid != 0:
        self.send_to_pacman('n')
      (self.pid, self.exit_status) = os.wait()

      pattern = '\n'
      results = re.split(pattern, out)

      for result in results:
        if result != '' and result.startswith('Targets'):
          out = result
          pattern2 = '\s'
          
          results2 = re.split(pattern2, result)

          for result2 in results2[1:]:
            first_dash = result2.index('-')
            last_dash = result2.rindex('-')
            before_last_dash = result2[:last_dash].rindex('-')

            name = result2[:before_last_dash]
            version = result2[before_last_dash+1:last_dash]

            #updates.append((name, version))
            updates.append(name)
            
          #print 'update list: ', updates

      ret_err = self.pacman.get_err_pipe().read()
      #print 'ret_err: ', ret_err
      return updates, out
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
      self.run_pacman_with('-Ss')
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
    
  # def local_search(self, what= ''): {{{
  def local_search(self, what= ''):
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
      return all
    else:
      (self.pid, self.exit_status) = os.wait()
      return None
  # }}}
  
  # def repofiles2(self): {{{
  def repofiles2(self):
    self.run_pacman_with('-Ss')

    if self.pacman.get_pipeit() == True:

      list = self.pacman.get_read_pipe().read()
      #(all, pkgs) = self.__compile_from_repo_list_dict_2__(list)
      (all, pkgs) = self.__compile_pkg_dict_2__(list)

      (self.pid, self.exit_status) = os.wait()
      return (all, pkgs)
    else:
      (self.pid, self.exit_status) = os.wait()
      return None
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

  # def __capture_output__(self): {{{
  def __capture_output__(self):
    line = 'a'
    out = ''

    stream = None

    if self.pacman.get_pipeit():
      #print 'read_pipe'
      stream = self.pacman.get_read_pipe()
    else:
      #print 'stdout'
      stream = sys.stdout

    while len(line) == 1:
      #print stream
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
    
    regex = re.compile('is up to date')
    match = regex.search(out)

    if not match:
      return (False, out)
    elif match.span() != (0,0):
      return (True, out)
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

  # def install_part_1(self, what = ''): {{{
  def install_part_1(self, what = ''):
    if not self.__is_root__():
      print "You are not ROOT. Bye bye."
      return
    if what == '':
      print 'Please specify a package to install'
      return

    self.run_pacman_with('-S ' + what)

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

      return (found, output)
    else:
      return (False, None)
  # }}}

  # def install_part_2(self, txt_to_pacman): {{{
  def install_part_2(self, txt_to_pacman):
    self.send_to_pacman(txt_to_pacman)
    # HACK
    (self.yesno, out) = self.__read_and_check_for_yesno__()

    return out
  # }}}
  
  # def install_part_3(self, txt_to_pacman): {{{
  def install_part_3(self, txt_to_pacman): 
    self.send_to_pacman(txt_to_pacman)
    # HACK
    (self.yesno, out) = self.__read_and_check_for_yesno__()

    (self.pid, self.exit_status) = os.wait()
    
    return (self.exit_status, (self.yesno, out))
  # }}}

  # def install_part_2_no_wait(self, txt_to_pacman): {{{
  def install_part_2_no_wait(self, txt_to_pacman):
    self.send_to_pacman(txt_to_pacman)
    # HACK
    out = self.__read_and_check_for_yesno__()

    return out
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

  # def install_packages_noconfirm(self, what = ''): {{{
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
  
  # def local_info(self, what = ''): {{{
  def local_info(self, what = ''):
    if what == '':
      print 'Please specify a package to query for info'
      return
    
    self.run_pacman_with('-Qi ' + what)
    
    if self.pacman.get_pipeit() == True:
      list = self.pacman.get_read_pipe().read()

      if list == '\n':
        (self.pid, self.exit_status) = os.wait()
        return None

      all = self.__compile_pkg_info__(list)

      (self.pid, self.exit_status) = os.wait()
      return all
    else:
      (self.pid, self.exit_status) = os.wait()
      return None

  # }}}
  
  # def info(self, what = ''): {{{
  def info(self, what = ''):
    if what == '':
      print 'Please specify a package to query for info'
      return
    
    self.run_pacman_with('-Si ' + what)
    
    if self.pacman.get_pipeit() == True:
      list = self.pacman.get_read_pipe().read()

      all = self.__compile_pkg_info__(list)

      (self.pid, self.exit_status) = os.wait()
      return all
    else:
      (self.pid, self.exit_status) = os.wait()
      return None
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
    return (self.exit_status, dependencies, out)
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
# }}}

# main {{{
if __name__ == '__main__':
  s = shell(sys.argv[1:], True)
  #s = shell(sys.argv[1:], False)
  #s = shell(sys.argv[1:], False, False)
  s.go()
# }}}

