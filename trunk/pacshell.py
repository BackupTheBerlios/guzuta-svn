#! /usr/bin/env python
# -*- coding: UTF-8 -*

import pipes
import sys
import getopt
import os
import string
import posix

class pacman:
  def __init__(self, args, pacman_location = '/usr/bin/pacman'):
    self.args = args
    self.executable = pacman_location
  
  def run(self):
    """Runs pacman and returns the stdout and stderr streams with the
    specified args"""
    child_stdin, child_stdout_and_stderr = os.popen4(self.executable + ' ' + \
        self.args)
    return child_stdout_and_stderr
    #lines = child_stdout_and_stderr.readlines()
  
    
class pacshell:
  def __init__(self, command_line):
    uid = posix.getuid()
    #if uid != 0:
    #  print "You are not ROOT. Root access is required to operate this."
    #  print "For now."
    #  sys.exit(127)
    self.pacman = '/usr/bin/pacman'
    self.runable = self.pacman
    self.opt_names = 'h:j:k:'
    self.long_opt_names = ''
    self.PS1 = "#"
    self.prompt = "Welcome to pacshell!\n" + self.PS1 + " "
    self.commands = ['localsearch']
    
    self.opts , self.long_opts = getopt.getopt(command_line, self.opt_names,
        self.long_opt_names)
    
    #print 'opts = ' + str(self.opts)
    #print 'long_opts = ' + str(self.long_opts)

  def run_pacman(self, args):
    child_stdin, child_stdout_and_stderr = os.popen4(self.runable + ' ' + args)
    lines = child_stdout_and_stderr.readlines()
    #for line in lines:
    #  print line[0 : len(line) - 1]
      
  def localsearch(self, args):
    self.run_pacman('-Ss ' + args)

  def read_command(self):
    try:
      ret = raw_input(self.prompt)
    except KeyboardInterrupt:
      print "\nInterrupted!"
      sys.exit(0)
    except EOFError:
      print "\nEOF!"
      sys.exit(0)
      
    return ret

  def shell(self):
    while(True):
      ret = self.read_command()
      print ret
      if ret in self.commands:
        print 'yay'
    
    
   #try:
   #    opts, args = getopt.getopt(argv, "hg:s", ["help", "grammar="])
   #except getopt.GetoptError:
   #    usage()
   #    sys.exit(2)
   #for opt, arg in opts:
   #    if opt in ("-h", "--help"):
   #        usage()
   #        sys.exit()
   #    elif opt == '-d':
   #        global _debug
   #        _debug = 1
   #    elif opt in ("-g", "--grammar"):
   #        grammar = arg
   #  
if __name__ == '__main__':
  try:
    ps = pacshell(sys.argv[1:])
    ps.run_pacman('-Ss bash')
    ps.shell()
  except getopt.GetoptError:
    print "no args"
    sys.exit(2)
