#! /usr/bin/env python
# -*- coding: UTF-8 -*

from os import popen2
import sys

def pipe_processor(pipe_cmd, out):
    """Call proc(out_stream) passing the output sent to
    out_stream to the command specified by pipe_cmd.
    Output from pipe_cmd is sent to out"""
    to_pipe, from_pipe = popen2(pipe_cmd, "w")
    # read what was written and spit it to the specified out.
    to_pipe.writelines(['bla\n', 'ble\n'])
    to_pipe.close()
    for i in from_pipe:
      print >>out, i[0: len(i) - 1]
    from_pipe.close()
    return None

if __name__ == '__main__':
  pipe_processor('cat', sys.stdout)

