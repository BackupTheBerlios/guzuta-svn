#! /usr/bin/env python
# -*- coding: UTF-8 -*

import os, sys

if __name__ == '__main__':
  line = sys.stdin.readline()

  while line != "":
    sys.stdout.write('OUT!: <' + line[0: len(line)-1] + '>')
    line = sys.stdin.readline()

