#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim: set foldmethod=marker:

import os,sys,select

if __name__ == '__main__':
  (rf,wf) = os.pipe()
  rfp = os.fdopen(rf, 'r')
  wfp = os.fdopen(wf, 'w')
  wfp.write('the\n')
  wfp.write('spanish\n')
  wfp.write('inquisition\n')
  wfp.flush()
  print 'write pipe primed with 3 messages'

  for i in range(3):
    print 'Select on read handle:', select.select([rfp], [], [], 0)[0]
    print '... and read yields:', rfp.readline()[:-1]
