 #!/usr/bin/env python
 """Show a shell command's output in a gtk.TextView without freezing the UI"""

 import os, threading, locale

 import pygtk
 pygtk.require('2.0')
 import gtk

 encoding = locale.getpreferredencoding()
 utf8conv = lambda x : unicode(x, encoding).encode('utf8')

 def on_button_clicked(button, buffer, command):
     thr = threading.Thread(target= read_output, args=(buffer, command))
     thr.run()
    
 def read_output(buffer, command):
     stdin, stdouterr = os.popen4(command)
     for line in stdouterr.readlines():
          buffer.insert(buffer.get_end_iter(), utf8conv(line))

 sw = gtk.ScrolledWindow()
 sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
 textview = gtk.TextView()
 textbuffer = textview.get_buffer()
 sw.add(textview)
 win = gtk.Window()
 win.resize(300,500)
 win.connect('delete-event', gtk.main_quit)
 button = gtk.Button("Press me!")
 command = 'dir -R %s' % os.getcwd()
 button.connect("clicked", on_button_clicked, textbuffer, command)
 vbox = gtk.VBox()
 vbox.pack_start(button, gtk.FALSE)
 vbox.pack_start(sw)
 win.add(vbox)
 win.show_all()

 gtk.main()
