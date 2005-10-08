#!/usr/bin/env python
import socket
import gobject
import gtk
import signal
import time

window = gtk.Window()
tv = gtk.TextView()
window.set_geometry_hints(geometry_widget=None, base_width=600, base_height=600, max_width=600, max_height=600)
window.add(tv)

def get_file():
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.settimeout(15)
  sock.connect(('pygtk.org', 80))
  sock.send('GET /index.html HTTP/1.1\nHost: pygtk.org\n\n')
  return sock

def handle_data(source, condition):
  #print 'handle_data!'
  data = source.recv(1)
  #print len(data)
  if len(data) > 0:
    buffer = tv.get_buffer()
    buffer.insert_at_cursor(data)
    return True #run forever
  else:
    print 'closed'
    print 'so get new data...'
    sock = get_file()
    gobject.io_add_watch(sock, gobject.IO_IN, handle_data)
    return False # stop looping

sock = get_file()
gobject.io_add_watch(sock, gobject.IO_IN, handle_data)

#w = gtk.Window()
#w.set_border_width(15)
#msg = '''\
#    Play with resizing the window...
#
#RESULT:
#It will only block on sock.connect()
#which is normal because to use the socket you have to connect
#here we wait for maximum 15 seconds and then we timeout'''
#w.add(gtk.Label(msg))
#w.show_all()
window.show_all()
signal.signal(signal.SIGINT, signal.SIG_DFL) # ^C exits the application
gtk.main()
