"""Run a subprocess and communicate with it via stdin, stdout, and stderr.

Requires that platform supports, eg, posix-style 'os.pipe' and 'os.fork'
routines.

Subprocess class features:

- provides non-blocking (but slow, char-by-char), stdin and stderr reads

- *not* dependent (but capitalizes) on python 1.2 and later, but

- regular, non-blocking 'readline()' as fast as regular, *if* python version
supports stdio buffer-size regulation, ie python v 1.2 or later on posix.

- provides subprocess stop and continue, kill-on-deletion

- provides (kludgy) detection of subprocess startup failure - see
implementation notes in the code; suggestions sought!

- Subprocess objects have nice, informative string rep (as every good object
ought)."""

__version__ = "$Revision: 1.2 $"

# $Id: subproc.py,v 1.2 1995/01/12 21:39:07 klm Exp $
# Originally by ken manheimer, ken.manheimer@nist.gov, jan 1995.

# Prior art: Initially based python code examples demonstrating usage of pipes
# and subprocesses, primarily one by jose pereira.

# Implementation notes:
# - I'm not using the fcntl module to implement non-blocking file descriptors,
# because i don't know what all in it is portable and what is not. I'm not
# about to provide for different platform contingencies - at that extent, the
# effort would be better spent hacking 'expect' into python.
# - Todo? - Incorporate an error-output handler approach, where error output is
# checked on regular IO, when a handler is defined, and passed to the
# handler (eg for printing) immediately as it shows...
# - Detection of failed subprocess startup is a gross kludge, at present.
# I, however, do not know a simple, clean (and portable) way to do so.
# (All i really need is an (entirely) non-intrusive way to tell when the
# execvp has executed successfully, i can have the parent block looking for
# either that or the failure.) Suggestions welcome!!
#
# ken.manheimer@nist.gov

import sys, os, string, time
from select import select

SubprocessError = 'SubprocessError'
# You may need to increase execvp_grace_seconds, if you have a large or slow
# path to search:
execvp_grace_seconds = 1

try:
  # Try opening a spare file descriptor with the python 1.2-and-up
  # buffer-size option. (Extraneous files are discarded.)
  os.fdopen(os.pipe()[0], 'r', 0)
  has_buffer_control = 1
except:
  has_buffer_control = 0

class Subprocess:
"""Run and communicate asynchronously with a subprocess.

Provides non-blocking reads in the form of '.readPendingChars' and
'.readPendingLine', though they're both slow because they do
character-at-at-time reads.

The '.readline' may be faster (if the python version has stdio buffer-size
regulation, ie python 1.2 or later), but in any case it will block until it
gets a complete line.

'.peekPendingChar' does a non-blocking, non-consuming read for pending
output, and can be used before '.readline' to check non-destructively for
pending output."""

  pid = 0
  cmd = ''
  peekedChar = '' # Single-char buffer for peek
  expire_noisily = 1 # Announce subproc destruction?

  def __init__(self, cmd, expire_noisily=0):
    """Launch a subprocess, given command string COMMAND."""
    self.cmd = cmd
    self.pid = 0
    self.expire_noisily = expire_noisily
    self.fork()

  def fork(self, cmd=None):
    """Fork a subprocess with designated COMMAND (default, self.cmd)."""
    if cmd: self.cmd = cmd
    else: cmd = self.cmd
    cmd = string.split(self.cmd)
    pRc, cWp = os.pipe() # parent-read-child, child-write-parent
    cRp, pWc = os.pipe() # child-read-parent, parent-write-child
    pRe, cWe = os.pipe() # parent-read-error, child-write-error

    self.pid = os.fork()

    if self.pid == 0: #### CHILD ####
      parentErr = os.dup(2) # Preserve handle on *parent's* stderr
      # Reopen stdin, out, err, on pipe ends:
      os.dup2(cRp, 0) # cRp = sys.stdin
      os.dup2(cWp, 1) # cWp = sys.stdout
      os.dup2(cWe, 2) # cWe = sys.stderr
      # Ensure (within reason) stray file descriptors are closed:
      for i in range(4,100):
        if i != parentErr:
          try: os.close(i)
          except: pass

try: # Exec the command:
os.execvp(cmd[0], cmd) # >*<
os._exit(1) # Shouldn't get here # ***>

except:
os.dup2(parentErr, 2) # Reconnect to parent's stdout
sys.stderr.write("**execvp failed, '%s'**\n" %
str(sys.exc_value))
os._exit(1) # ***>
os._exit(1) # Shouldn't get here. # ***>

else: ### PARENT ###
# Connect to the child's file descriptors, using our customized
# fdopen:
self.tochild = fdopen(pWc, 'w')
self.fromchild = fdopen(pRc, 'r')
self.errfromchild = fdopen(pRe, 'r')
time.sleep(execvp_grace_seconds)
if not self.cont():
map(os.close, [pRc, cWp, cRp, pWc, pRe, cWe])
raise SubprocessError, "Subprocess '%s' failed." % self.cmd

### Write input to subprocess ###

def write(self, str):
"""Write a STRING to the subprocess."""

if not self.pid:
raise SubprocessError, "no child" # ===>
else:
if select([],[self.tochild],[],0)[1] != []:
self.tochild.write(str)
self.tochild.flush()
else:
raise os.IOError, "write to %s blocked" % self # ===>

def writeline(self, line=''):
"""Write STRING, with added newline termination, to subprocess."""
self.write(line + '\n')

### Get output from subprocess ###

def peekPendingChar(self):
"""Return, but (effectively) do not consume a single pending output
char, or return null string if none pending."""

if self.peekedChar: return self.peekedChar # ===>

self.peekedChar = readPendingChar(which)
return self.peekedChar # ===>

def consumePeekedChar(self):
"""Return previously peeked char, clearing it out of the pipe."""

peeked = self.peekedChar
self.peekedChar = ''
return peeked # ===>

def readPendingChars(self, doErrStrm=0):
"""Read all currently pending subprocess output as a single string."""

if not self.pid:
raise SubprocessError, "no child" # ===>
if doErrStrm: which = self.errfromchild; peeked = ''
else: which = self.fromchild; peeked = self.consumePeekedChar()
return peeked + readPendingChars(which) # ===>
def readPendingErrChars(self):
"""Read all currently pending subprocess error output as a single
string."""
return self.readPendingChars(1) # ===>

def readPendingLine(self, doErrStrm=0):
"""Read (non-blocking) currently pending subprocess output, up to a
complete line (newline inclusive)."""
if not self.pid:
raise SubprocessError, "no child" # ===>
if doErrStrm: which = self.errfromchild; peeked = ''
else: which = self.fromchild; peeked = self.consumePeekedChar()
return peeked + readPendingLine(which)
def readPendingErrLine(self):
"""Read (non-blocking) currently pending subprocess error output, up to
a complete line (newline inclusive)."""
return self.readPendingLine(1) # ===>

def readline(self, doErrStrm=0):
"""Return next complete line of subprocess output. *Block* until then.

NOTE: In python version with stdio buffer-size regulation (v 1.2 and
later), there is a speed advantage to using this routine, as long as
you're assured of receiving an entire line. On those systems, this
call will chunk line reads, rather than python getting the characters
one-at-a-time."""

if not self.pid:
raise SubprocessError, "no child" # ===>
if doErrStrm: which = self.errfromchild; peeked = ''
else: which = self.fromchild; peeked = self.consumePeekedChar()
return peeked + readline(which)
def readlineErr(self):
"""Return next line of subprocess error output."""
return self.readline(1)

### Subprocess Control ###

def status(self):
"""Return string indicating whether process is alive or dead."""
if not self.cmd:
status = 'sans command'
elif not self.pid:
status = 'sans process'
elif not self.cont():
status = "(unresponding) '%s'" % self.cmd
else:
status = "'%s'" % self.cmd
return status

def stop(self, verbose=1):
"""Signal subprocess with STOP (17), returning 'stopped' if ok, or 0
otherwise."""
try:
os.kill(self.pid, 17)
if verbose: print "Stopped '%s'" % self.cmd
return 'stopped'
except os.error:
if verbose:
print "Stop failed for '%s' - '%s'" % (self.cmd, sys.exc_value)
return 0
def cont(self, verbose=0):
"""Signal subprocess with CONT (19), returning 'continued' if ok, or 0
otherwise."""
try:
os.kill(self.pid, 19)
if verbose: print "Continued '%s'" % self.cmd
return 'continued'
except os.error:
if verbose:
print ("Continue failed for '%s' - '%s'" %
(self.cmd, sys.exc_value))
return 0

def die(self):
"""Send process PID signal SIG (default 9, 'kill'), returning 0 if
process is gone afterwards.

If process is not killed:
- return 'missed' if 'os.kill' raised an error
- return 'no effect' if os.kill hit, but subsequent continue signal
also hits."""
if not self.pid:
raise SubprocessError, "No process" # ===>
elif not self.pid or not self.cont():
raise SubprocessError, "Process already defunct" # ===>

# Try sending first a TERM and then a KILL signal.
keep_trying = 1
for sig in [('TERM', 15), ('KILL', 19), ()]:
if not sig:
raise SubprocessError, ("Failed to kill subproc %d, '%s'" %
(self.pid, self.cmd)) # ===>
try:
os.kill(self.pid, sig[1])
# Try sending a CONT signal, to establish absence of subproc:
try:
os.kill(self.pid, 19)
if self.expire_noisily: print "kill via %s failed" % sig[0]
except:
break # Subproc gone.
except:
raise SubprocessError, ("Can't signal subproc %d, '%s'" %
(self.pid, self.cmd)) # ===>

if self.expire_noisily: print "\n(Killed '%s')" % self.cmd
self.pid = 0
return None
def __del__(self):
"""Terminate the subprocess"""
if self.pid:
self.die()
def __repr__(self):
status = self.status()
return '<Subprocess ' + status + ', at ' + hex(id(self))[2:] + '>\n'

# We have two definitions for readPending, one which depends on the file being
# opened with 0 buffer size, which requires python 1.2 or later, the other
# which circumvents stdio, but reads and appends the input one character at a
# time.

if has_buffer_control:

def readPendingChar(file):
"""Return single character of pending output from file, or empty string
if none."""
if select([file], [],[], 0)[0]:
return file.read(1)
else: return '' # ===>

def readPendingChars(file):
"""Return pending output from FILE, or empty string if nothing pending.

Non-hanging operation depends on the file having been opened with
buffer size 0!"""

got = nother = ''
while select([file], [],[], 0)[0]:
nother = file.read(1)
got = got + nother
return got # ===>

def readPendingLine(file):
"""Return pending output from FILE, up to a newline (inclusive)."""

got = nother = ''
while select([file], [],[], 0)[0] and nother != '\n':
nother = file.read(1)
got = got + nother
return got # ===>

def readline(file):
"""Return next output line from file, blocking until it is received.

NOTE that this will chunk reads using file.readline, so it should be
more efficient than readPendingLine, for when you're willing to
block."""
return file.readline()

def fdopen(fd, mode):
"""Custom wrapper for fdopen, to open with 0 buffer size."""

return os.fdopen(fd, mode, 0)

else: # not has_buffer_control:

def readPendingChar(file):
"""Return single character of pending output from file, or empty string
if none."""
fd = file.fileno()
if select([fd], [],[], 0)[0]:
return os.read(fd, 1)
else: return ''

def readPendingChars(file):
"""Return pending output in FILE, or empty string if nothing pending.

This circumvents stdio, for python versions that do not have the
buffer-size option on fdopen and open."""

fd = file.fileno()
got = nother = ''
while select([fd], [],[], 0)[0]:
nother = os.read(fd, 1)
got = got + nother
return got # ===>

def readPendingLine(file):
"""Return pending output from FILE, up to a newline (inclusive)."""

fd = file.fileno()
got = nother = ''
while select([fd], [],[], 0)[0] and nother != '\n':
nother = os.read(fd, 1)
got = got + nother
return got # ===>

def readline(file):
"""Return next output line from file, blocking until it is received.

NOTE that this is as slow as readPendingLine (and blocks, besides),
ultimately because this version of python does not, evidently, support
stdio buffer-size regulation (ie, is prior to python 1.2)."""

got = ''
while got[-1] != '\n':
select([file], [],[]) # Block pending some output.
got = got + readPendingLine(file)
return got

def fdopen(fd, mode):
"""Trivial wrapper for fdopen, does nothing special since we're running
in a python that lacks stdio buffer-size control."""

return os.fdopen(fd, mode)

def test():
print "\tOpening subprocess:"
p = Subprocess('cat', 1) # set to expire noisily...
print p
print "\tOpening bogus subprocess, should fail:"
try:
b = Subprocess('/', 1)
print "\tOops! Null-named subprocess startup *succeeded*?!?"
except SubprocessError:
print "\t...yep, it failed."
print '\tWrite, then read, two newline-teriminated lines, using readline:'
p.write('first full line written\n'); p.write('second.\n')
print p.readline()[:-1]
print p.readline()[:-1]
print '\tThree lines, last sans newline, read using combination:'
p.write('first\n'); p.write('second\n'); p.write('third, (no cr)')
print '\tFirst line via readline:'
print p.readline()[:-1]
print '\tRest via readPendingChars:'
print p.readPendingChars()
print "\tStopping then continuing subprocess (verbose):"
if not p.stop(1): # verbose stop
print '\t** Stop seems to have failed!'
else:
print '\tWriting line while subprocess is paused...'
p.write('written while subprocess paused\n')
print '\tNonblocking read of paused subprocess (should be empty):'
print p.readPendingChars()
print '\tContinuing subprocess (verbose):'
if not p.cont(1): # verbose continue
print '\t** Continue seems to have failed! Probly lost subproc...'
return p
else:
print '\tReading accumulated line, blocking read:'
print p.readline()
print "\tExiting, should get a 'killed ...' message as p is freed."
return None
