#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim: set foldmethod=marker:

# imports {{{
import pygtk
pygtk.require('2.0')
import gtk
import gtk.gdk
if gtk.pygtk_version < (2,3,90):
  raise SystemExit
import gobject
import gtk.glade
import pango, sys, os, os.path, posix, re, threading, thread, time, glob

# "our" trayicon
import trayicon
import signal

from shell import *
# }}}

# def xor_two_dicts(a, b): {{{
def xor_two_dicts(a, b):
  ret = {}
  not_ret = {}

  # if key,value exist in both dicts, scrap
  # else put it in ret
  for key, value in a.iteritems():
    try:
      b[key]
      not_ret[key] = value
    except KeyError:
      ret[key] = value

  for key, value in b.iteritems():
    try:
      not_ret[key]
    except KeyError:
      try:
        a[key]
      except KeyError:
        ret[key] = value

  return ret
# }}}
    
# class gui: {{{
class gui:
  pango_no_underline = 0
  pango_underline_single = 1

  # def progress_timeout(self, progress_bar): {{{
  def progress_timeout(self):
    if self.busy_window_hidden == False:
      self.busy_progress_bar.pulse()
    return True
  # }}}

  # def try_sem(self): {{{
  def try_sem(self):
    while self.th != None and self.th.isAlive() == True:
      time.sleep(0.1)
  # }}}

  # def try_sem_animate_progress_bar(self): {{{
  def try_sem_animate_progress_bar(self):
    #console_expander = self.all_widgets.get_widget('console_expander')
    #console_expander.set_expanded(False)

    #print 'uuu.'
    #read_pipe = self.shell.get_read_pipe()
    #err_pipe = self.shell.get_err_pipe()
    #print 'pipes: ', (read_pipe, err_pipe)
    #if read_pipe != None and err_pipe != None:
    #  gobject.io_add_watch(read_pipe, gobject.IO_IN, self.pipe_read_ready)
    #  gobject.io_add_watch(err_pipe, gobject.IO_IN, self.pipe_read_ready)
    #print 'pipes after: ', (read_pipe, err_pipe)
    
    #self.busy_window = self.all_widgets.get_widget('busy_window')
    self.busy_window = self.all_widgets.get_widget('busy_window2')
    
    #self.busy_dialog = self.all_widgets.get_widget('busy_dialog')
    
    #self.busy_progress_bar = self.all_widgets.get_widget('busy_progress_bar')
    self.busy_progress_bar = self.all_widgets.get_widget('busy_progress_bar2')
    
    self.busy_progress_bar.set_fraction(0.0)

    self.main_window.set_sensitive(False)

    self.busy_window_hidden = False
    self.busy_window.show_all()
    self.busy_window_on = True

    if self.th:
      while self.th.isAlive() == True:
        while gtk.events_pending():
          gtk.main_iteration(False)
        #if self.stop_pulsing:
        #  self.busy_window.hide()
        #  self.busy_window_hidden = True
        #  self.busy_window_on = False
        #  self.main_window.set_sensitive(True)
        #  print 'th: ', self.th
        time.sleep(0.01)
    #print 'update done.'

    self.busy_window.hide()
    self.busy_window_hidden = True
    self.busy_window_on = False

    #console_expander.set_expanded(False)
    
    self.main_window.set_sensitive(True)
  # }}}

  # def run_in_thread(self, method, args_dict, wait=False): {{{
  def run_in_thread(self, method, args_dict, wait=False):
    self.lock = threading.Lock()
    args_dict['lock'] = self.lock
    self.th = threading.Thread(target=method, kwargs=args_dict)
    self.th.start()
    if wait:
      th.join()
  # }}}

  # def __setup_pkg_treeview__(self): {{{
  def __setup_pkg_treeview__(self):
    # checked, name, version, description 
    self.liststore = gtk.ListStore('gboolean', str, str, str)

    self.textrenderer = gtk.CellRendererText()
    self.togglerenderer = gtk.CellRendererToggle()
    self.togglerenderer.set_active(True)

    self.togglerenderer.connect('toggled', self.toggled)

    self.emptycolumn = gtk.TreeViewColumn('Selected')
    self.emptycolumn.set_sort_column_id(0)
    self.emptycolumn.pack_start(self.togglerenderer)
    self.emptycolumn.set_attributes(self.togglerenderer, active=0)
    
    #self.repositorycolumn = gtk.TreeViewColumn('Repository')
    #self.repositorycolumn.set_sort_column_id(1)
    #self.repositorycolumn.pack_start(self.textrenderer)
    #self.repositorycolumn.set_attributes(self.textrenderer, text=1)
    
    self.namecolumn = gtk.TreeViewColumn('Name')
    self.namecolumn.set_sort_column_id(1)
    self.namecolumn.pack_start(self.textrenderer)
    self.namecolumn.set_attributes(self.textrenderer, text=1)
    
    self.installedversioncolumn = gtk.TreeViewColumn('Installed')
    self.installedversioncolumn.set_sort_column_id(2)
    self.installedversioncolumn.pack_start(self.textrenderer)
    self.installedversioncolumn.set_attributes(self.textrenderer, text=2)
    
    self.availableversioncolumn = gtk.TreeViewColumn('Available')
    self.availableversioncolumn.set_sort_column_id(3)
    self.availableversioncolumn.pack_start(self.textrenderer)
    self.availableversioncolumn.set_attributes(self.textrenderer, text=3)
    
    #self.packagercolumn = gtk.TreeViewColumn('Packager')
    #self.packagercolumn.set_sort_column_id(5)
    #self.packagercolumn.pack_start(self.textrenderer)
    #self.packagercolumn.set_attributes(self.textrenderer, text=5)

    self.treeview.append_column(self.emptycolumn)
    #self.treeview.append_column(self.repositorycolumn)
    self.treeview.append_column(self.namecolumn)
    self.treeview.append_column(self.installedversioncolumn)
    self.treeview.append_column(self.availableversioncolumn)

    #self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
    # positions are as follows:
    # name, version, description
    # TODO: sort this
    #print self.local_pkgs
    keys = self.local_pkgs.keys()
    keys.sort()
    for k in keys:
      v = self.local_pkgs[k]
    #for k,v in self.local_pkgs.iteritems():
      #available version
      try:
        available_version = self.pkgs[k][1]
      except KeyError:
        # pkg was installed separately)
        available_version = '--'
        
      self.liststore.append([False, k, v[1], available_version])
    #for i in range(2):
    #  self.liststore.append([False, 'a', 'b', 'c'])
  
    self.treeview.set_model(self.liststore)
  # }}}
  
  # def __setup_repo_treeview__(self): {{{
  def __setup_repo_treeview__(self):
    self.treestore_repos = gtk.TreeStore(str)

    self.textrenderer_repos = gtk.CellRendererText()
    self.textrenderer_repos.set_property('weight', 400)

    self.repocolumn = gtk.TreeViewColumn('Repositories')
    self.repocolumn.set_sort_column_id(1)
    self.repocolumn.pack_start(self.textrenderer_repos)
    self.repocolumn.set_attributes(self.textrenderer_repos, text=0)
    
    self.treeview_repos.append_column(self.repocolumn)
    
    self.treestore_repos.set_sort_column_id(0, gtk.SORT_ASCENDING)

    iter0 = self.treestore_repos.append(None, ['Pseudo Repos'])
    self.treestore_repos.append(iter0, ['All'])
    self.treestore_repos.append(iter0, ['Installed'])
    self.treestore_repos.append(iter0, ['Not Installed'])
    #self.treestore_repos.append(iter0, ['Explicitly Installed'])
    #self.treestore_repos.append(iter0, ['Last Installed'])
    #self.treestore_repos.append(iter0, ['Last Uninstalled'])

    iter1 = self.treestore_repos.append(None, ['Repos'])
    for repo, v in self.pkgs_by_repo.iteritems():
      repo = repo.capitalize()
      self.treestore_repos.append(iter1, [repo])
    
    self.treeview_repos.set_model(self.treestore_repos)
    self.treeview_repos.expand_all()
  # }}}

  # def set_pkg_update_alarm(self, alarm_time, time_type): {{{
  def set_pkg_update_alarm(self, alarm_time, time_type):
    # unschedule the alarm
    #signal.alarm(0)

    #self.pkg_update_alarm = 60 * 60 # 60 minutes
    if time_type == 1:
      # hours
      self.pkg_update_alarm = alarm_time
      self.pkg_update_alarm_period = 1
      #print 'setting alarm to: ', alarm_time * 60 * 60
      #signal.alarm(alarm_time * 60 * 60)
    else:
      # dangerous, don't let this be less than a good number, like say 40
      # minutes. if so, warn
      if alarm_time < 40:
        generic_cancel_ok = self.all_widgets.get_widget('generic_cancel_ok')
        self.current_dialog = generic_cancel_ok
        generic_cancel_ok_label =\
          self.all_widgets.get_widget('generic_cancel_ok_label')
        text = """<b>Warning</b>\nThe time lapse between automatic update checks
        is very short.\nAre you sure you want to keep this value?"""
        generic_cancel_ok_label.set_markup(text)

        self.current_dialog_on = True
        response = generic_cancel_ok.run()
        generic_cancel_ok.hide()
        self.current_dialog_on = False
        if response == gtk.RESPONSE_OK:
          self.pkg_update_alarm = alarm_time
          self.pkg_update_alarm_period = 0
          #print 'setting alarm to: ', alarm_time * 60
          #signal.alarm(alarm_time * 60)
        else:
          pass
      else:
        self.pkg_update_alarm = alarm_time
        self.pkg_update_alarm_period = 0
        #print 'setting alarm to: ', alarm_time * 60
        #signal.alarm(alarm_time * 60)
  # }}}

  # def __expand_deps_list__(self, deps_list): {{{
  def __expand_deps_list__(self, deps_list):
    prefix = '/var/cache/pacman/pkg/'
    
    ret = []
    for dep in deps_list:
      full_path = os.path.join(prefix, dep)
      matches = glob.glob(full_path + '*gz')
      
      # get latest version of dep
      matches.sort(lambda x,y: cmp(x.lower(), y.lower()), str.lower, True)
      ret.append(matches[0])
    return ret
  # }}}

  # def pipe_read_ready(self, source, cb_condition): {{{
  def pipe_read_ready(self, source, cb_condition):
    print 'argh!'
    #gtk.gdk.threads_enter()
    if cb_condition == gobject.IO_IN:
      print 'busy_window_on: ', self.busy_window_on
      if self.busy_window_on:
        print 'ready to output something.'
        data = source.read(1)
        print 'char read: ', data
        console_textview = self.all_widgets.get_widget('console_textview')
        buffer = console_textview.get_buffer()

        buffer.insert_at_cursor(data)
        if len(data) > 0:
          gtk.gdk.threads_leave()
          return True
        else:
          gtk.gdk.threads_leave()
          return False
    #gtk.gdk.threads_leave()
  # }}}

  # def __init__(self, read_pipe = None, write_pipe = None): {{{
  def __init__(self, read_pipe = None, write_pipe = None):
    # signals !!!
    #fname = '/usr/share/guzuta/guzuta2.glade'
    gtk.gdk.threads_init()
    
    gtk.gdk.threads_enter()
    self.th = None
    self.stop_pulsing = False

    self.cwd = os.environ['PWD']

    #print 'working in: ', self.cwd
    
    #fname = '/usr/share/guzuta/guzuta3.glade'
    fname = self.cwd + '/share/guzuta/guzuta3.glade'
    if os.path.exists(fname):
      self.glade_file = fname
      #print 'fname: ', fname
    elif os.path.exists('/usr/share/guzuta/guzuta3.glade'):
      fname = '/usr/share/guzuta/guzuta3.glade'
      self.glade_file = fname
      #print 'fname: ', fname
    elif os.path.exists('guzuta3.glade'):
      fname = 'guzuta3.glade'
      self.glade_file = fname
      #print 'fname: ', fname
    else:
        print __name__
        print os.getcwd()
        print 'no glade file found!'
        sys.exit(2)

    # signals_dict {{{
    signals_dict = {\
    #'on_treeview_row_activated': self.on_row_activated,
    'on_treeview_cursor_changed': self.on_cursor_changed,
    'on_treeview_select_cursor_row': self.on_select_cursor_row,
    'on_treeview_repos_cursor_changed': self.on_cursor_changed,
    'on_treeview_repos_select_cursor_row': self.on_select_cursor_row,
    'on_mainwindow_delete_event': self.on_delete_event,
    'on_mainwindow_destroy_event': self.on_destroy,
    'on_update_db_popup_delete_event': self.on_update_db_popup_delete_event,
    'on_update_db_popup_destroy': self.on_destroy,
    'on_quit_activate': self.on_quit_activate,
    'on_update_db_clicked': self.on_update_db_clicked,
    #'on_okbutton_clicked': self.on_okbutton_clicked,
    'on_install_pkg_clicked': self.on_install_pkg_clicked,
    'on_remove_pkg_clicked': self.on_remove_pkg_clicked,
    #'on_okbutton2_clicked': self.on_okbutton2_clicked,
    'on_install_pkg_popup_delete_event': self.on_install_pkg_popup_delete_event,
    'on_install_pkg_popup_destroy': self.on_install_pkg_popup_destroy,
    'on_search_clicked': self.on_search_clicked,
    'on_clear_clicked': self.on_clear_clicked,
    'on_search_entry_activate': self.on_search_clicked,
    'on_about_activate': self.on_about_activate,
    'on_install_pkg_from_file_button_clicked':\
        self.on_install_pkg_from_file_activate,
    'on_install_pkg_from_file_activate':\
        self.on_install_pkg_from_file_activate,
    'on_pacman_log_activate': self.on_pacman_log_activate,
    'on_treeview_button_press_event': self.on_treeview_button_press_event,
    'on_install_popup_menu_activate': self.on_install_popup_menu_activate,
    'on_remove_popup_menu_activate': self.on_remove_popup_menu_activate,
    'on_systray_popup_menu_show_window_activate':\
        self.on_systray_popup_menu_show_window_activate,
    'on_systray_popup_menu_preferences_activate':\
        self.on_systray_popup_menu_preferences_activate,
    'on_systray_popup_menu_quit_activate':\
        self.on_systray_popup_menu_quit_activate,
    'on_preferences_clicked': self.on_preferences_clicked,
    'on_preferences_menu_activate': self.on_preferences_clicked,
    'on_preferences_pacman_log_button_clicked':\
        self.on_browse_preferences_button_clicked,
    'on_preferences_browser_button_clicked':\
        self.on_preferences_browser_button_clicked,
    'on_install_from_repo_button_clicked':\
        self.on_install_from_repo_button_clicked,
    'on_install_from_popup_menu_activate':\
        self.on_install_from_popup_menu_activate,
    'on_download_pkg_button_clicked':\
        self.on_download_pkg_button_clicked,
    'on_download_pkg_popup_menu_activate':\
        self.on_download_pkg_button_clicked,
    'on_cache_menu_activate':
      self.on_cache_menu_activate,
    'on_view_files_popup_menu_activate':
      self.on_view_files_popup_menu_activate,
    'on_busy_cancel_button_clicked':
      self.on_busy_cancel_button_clicked
    #'on_browse_preferences_button_clicked':\
    #    self.on_browse_preferences_button_clicked,
    #'on_information_text_enter_notify_event': self.on_hyperlink_motion,
    #'on_information_text_leave_notify_event':\
    #  self.on_mainwindow_motion_notify_event,
    #'on_mainwindow_enter_notify_event': self.on_mainwindow_enter_notify_event
    #'on_information_text_motion_notify_event': self.on_hyperlink_motion,
    #'on_mainwindow_motion_notify_event': self.on_mainwindow_motion_notify_event,
    #'on_systray_eventbox_button_press_event':\
    #    self.on_systray_eventbox_button_press_event,
    #'on_systray_eventbox_motion_notify_event':\
    #    self.on_systray_eventbox_motion_notify_event,
    #'on_systray_eventbox_leave_notify_event':\
    #    self.on_systray_eventbox_leave_notify_event
    }
    # }}}

    #self.pacman = pacman(self)
    self.pacman_events_queue = []
    self.treeview = None
    self.uid = posix.getuid()
    self.pkgs = {}
    self.local_pkg_info = {}
    self.remote_pkg_info = {}

    self.pkgs_by_repo = {}
    self.pkgs_by_repo['no repository'] = []

    self.url_tags = []
    self.underlined_url = False

    self.not_installed = {}
    self.trayicon = None
    self.systray_eventbox = None

    self.all_widgets = gtk.glade.XML(self.glade_file)

    self.systray_tooltips = gtk.Tooltips()
    self.systray_tooltips.enable()

    self.main_window_hidden = False
    self.busy_window_on = False
    self.busy_window_hidden = False
    self.current_dialog = None
    self.current_dialog_on = False
    self.current_dialog_hidden = False
    
    self.pacman_log_file = '/var/log/pacman.log'
    
    self.pkg_update_alarm = 2 # 2 hours
    self.pkg_update_alarm_period = 1 # hours

    self.browser = 'epiphany'

    self.read_conf()

    # setup the alarm handler
    #signal.signal(signal.SIGALRM, self.on_alarm)
    if self.pkg_update_alarm_period == 0:
      # minutes
      alarm_time = self.pkg_update_alarm * 60
    else:
      # hours
      alarm_time = self.pkg_update_alarm * 60 * 60
    #signal.alarm(alarm_time)

    self.shell = shell(command_line = None, pacman_events_queue =\
        self.pacman_events_queue, self.lock, interactive = True)
    self.populate_pkg_lists()
    # pid of pacman process
    self.pid = 0

    #self.textview = self.all_widgets.get_widget("textview")
    self.main_window = self.all_widgets.get_widget("mainwindow")
    #self.main_window.connect('enter_notify_event',\
    #    self.on_mainwindow_enter_notify_event)
    #self.open_menu_item = self.all_widgets.get_widget('open1')
    # checkbox, name, version, packager, description
    self.treeview = self.all_widgets.get_widget('treeview')
    # sortable
    self.treeview_repos = self.all_widgets.get_widget('treeview_repos')
    self.vbox2 = self.all_widgets.get_widget('vbox2')
    self.quit_item = self.all_widgets.get_widget('quit')
    self.update_db = self.all_widgets.get_widget('update_db')
    self.search_entry = self.all_widgets.get_widget('search_entry')
    
    #self.update_db_popup = self.all_widgets.get_widget('update_db_popup')
    #self.update_db_popup.hide()
    #self.install_pkg_popup = self.all_widgets.get_widget('install_pkg_popup')
    #self.install_pkg_popup.hide()

    #self.treemodel = self.treeview.get_model()
    
    #self.information_frame = self.all_widgets.get_widget("information_frame")
    self.information_text = self.all_widgets.get_widget('information_text')
    #self.information_text.connect('enter_notify_event',\
    #    self.on_hyperlink_motion)
    #self.information_text.connect('leave_notify_event',\
    #    self.on_mainwindow_motion_notify_event)

    #self.information_frame = gtk.Frame('ahaha')
    #self.vbox2.pack_end(self.information_frame)

    self.__setup_pkg_treeview__()
    self.__setup_repo_treeview__()

    self.all_widgets.get_widget('search_combobox').set_active(0)
    self.all_widgets.get_widget('cache_combobox').set_active(0)
    #TODO: implement when auto update works. alarm is giving a keyboarderror
    #self.all_widgets.get_widget('interval_preferences_combobox').set_active(0)
    
    #alarm_time = self.pkg_update_alarm / 60
    #spinbutton = self.all_widgets.get_widget('interval_preferences_spinbutton')
    #interval_preferences_combobox =\
    #  self.all_widgets.get_widget('interval_preferences_combobox')

    #interval_preferences_combobox.set_active(self.pkg_update_alarm_period)
    #spinbutton.set_value(alarm_time)

    self.all_widgets.signal_autoconnect(signals_dict)
    
    self.busy_window = None
    self.busy_window_hidden = True
    self.timer = gobject.timeout_add (100, self.progress_timeout)

    self.main_window.show()

    self.__build_trayicon__()
    # trayicon
    self.trayicon.show_all()
    
    if not self.__is_root__():
      #gtk.gdk.threads_enter()
      self.__disable_all_root_widgets__()
      not_root_dialog = self.all_widgets.get_widget('not_root_dialog')
      self.current_dialog = not_root_dialog

      self.main_window.set_sensitive(False)
      self.current_dialog_on = True
      not_root_dialog.run()
      not_root_dialog.hide()
      self.current_dialog_on = False
      self.main_window.set_sensitive(True)
      #gtk.gdk.threads_leave()
      #sys.exit(1)

    #print self.remote_pkg_info

    #gtk.gdk.threads_enter()
    #read_pipe = self.shell.get_read_pipe()
    #err_pipe = self.shell.get_err_pipe()
    #read_watch_id = gobject.io_add_watch(read_pipe, gobject.IO_IN,\
    #    self.pipe_read_ready)
    #err_watch_id = gobject.io_add_watch(err_pipe, gobject.IO_IN,\
    #    self.pipe_read_ready)
    #print 'registered'
    #print 'ids: ', (read_watch_id, err_watch_id)

    gtk.main()
    gtk.gdk.threads_leave()
  # }}}
  
  # def on_download_pkg_button_clicked(self, button): {{{
  def on_download_pkg_button_clicked(self, button):
    pkgs_to_download = self.get_all_selected_packages(self.liststore)

    if pkgs_to_download == []:
      return 
    
    self.download_packages_from_list(pkgs_to_download)
  # }}}
  
  # def on_browse_preferences_button_clicked(self, button): {{{
  def on_browse_preferences_button_clicked(self, button):
    pkg_filechooser_dialog =\
      self.all_widgets.get_widget('pkg_filechooser_dialog')
    self.current_dialog = pkg_filechooser_dialog

    #pkg_filechooser_dialog = gtk.FileChooserDialog('Open package file...',
    #    None,
    #    gtk.FILE_CHOOSER_ACTION_OPEN,
    #    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
    #      gtk.STOCK_OPEN, gtk.RESPONSE_OK))

    #pkg_filechooser_dialog.set_default_response(gtk.RESPONSE_OK)

    #preferences_pacman_log_file_text_entry =\
    #    self.all_widgets.get_widget('preferences_pacman_log_file_text_entry')

    preferences_pacman_log_file_text_entry =\
        self.all_widgets.get_widget('preferences_pacman_log_text_entry')

    self.current_dialog_on = True
    response = pkg_filechooser_dialog.run()
    pkg_filechooser_dialog.hide()
    self.current_dialog_on = False

    if response == gtk.RESPONSE_OK:
      preferences_pacman_log_file_text_entry.set_text(\
          pkg_filechooser_dialog.get_filename())
  # }}}

  # def on_preferences_browser_button_clicked(self, button): {{{
  def on_preferences_browser_button_clicked(self, button):
    pkg_filechooser_dialog =\
      self.all_widgets.get_widget('pkg_filechooser_dialog')
    self.current_dialog = pkg_filechooser_dialog

    #pkg_filechooser_dialog = gtk.FileChooserDialog('Open package file...',
    #    None,
    #    gtk.FILE_CHOOSER_ACTION_OPEN,
    #    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
    #      gtk.STOCK_OPEN, gtk.RESPONSE_OK))

    #pkg_filechooser_dialog.set_default_response(gtk.RESPONSE_OK)

    preferences_browser_text_entry =\
        self.all_widgets.get_widget('preferences_browser_text_entry')

    self.current_dialog_on = True
    response = pkg_filechooser_dialog.run()
    pkg_filechooser_dialog.hide()
    self.current_dialog_on = False

    if response == gtk.RESPONSE_OK:
      preferences_browser_text_entry.set_text(\
          pkg_filechooser_dialog.get_filename())
  # }}}
    
  # def on_preferences_clicked(self, button): {{{
  def on_preferences_clicked(self, button):
    interval_preferences_spinbutton =\
      self.all_widgets.get_widget('interval_preferences_spinbutton')
    
    interval_preferences_combobox =\
        self.all_widgets.get_widget('interval_preferences_combobox')
    
    #preferences_dialog = self.all_widgets.get_widget('preferences_dialog')
    preferences_dialog = self.all_widgets.get_widget('preferences_dialog')
    self.current_dialog = preferences_dialog

    #print self.pkg_update_alarm_period

    #print 'antes: ', self.pkg_update_alarm

    #TODO: implement when auto update works. alarm is giving a keyboarderror
    #interval_preferences_combobox.set_active(\
    #    self.pkg_update_alarm_period)

    #if self.pkg_update_alarm_period == 0:
    #  interval_preferences_spinbutton.set_value(\
    #      self.pkg_update_alarm)
    #  print 'depois: ', self.pkg_update_alarm
    #else:
    
    #TODO: implement when auto update works. alarm is giving a keyboarderror
    #interval_preferences_spinbutton.set_value(\
    #    self.pkg_update_alarm)
    
    #print 'depois: ', self.pkg_update_alarm

    #preferences_pacman_log_file_text_entry =\
    #    self.all_widgets.get_widget('preferences_pacman_log_file_text_entry')
    
    preferences_pacman_log_file_text_entry =\
        self.all_widgets.get_widget('preferences_pacman_log_text_entry')
    
    preferences_browser_text_entry =\
        self.all_widgets.get_widget('preferences_browser_text_entry')
        
    if self.pacman_log_file == '':
      log_file = '/var/log/pacman.log'
    else:
      log_file = self.pacman_log_file

    preferences_pacman_log_file_text_entry.set_text(log_file)
    preferences_browser_text_entry.set_text(self.browser)

    self.current_dialog_on = True
    preferences_dialog.run()
    preferences_dialog.hide()
    self.current_dialog_on = False

    #if interval_preferences_combobox.get_active() == 1:
    #  # hours
    #  self.set_pkg_update_alarm(\
    #      interval_preferences_spinbutton.get_value_as_int(), 1)
    #else:
    #  #print 'value of spinbutton: ',\
    #  interval_preferences_spinbutton.get_value_as_int()
    #  self.set_pkg_update_alarm(\
    #      interval_preferences_spinbutton.get_value_as_int(), 0)

    self.pacman_log_file = preferences_pacman_log_file_text_entry.get_text()

    self.browser = preferences_browser_text_entry.get_text()

    self.write_conf()

  # }}}
  
  # def on_alarm(self, signum, frame): {{{
  def on_alarm(self, signum, frame):
    # only do this if the main window is hidden !!!
    #print 'Alarm!'
    self.systray_tooltips.set_tip(self.systray_eventbox,\
        'Checking for updates...')
    if self.main_window_hidden():
      #ret, ret_err = self.shell.updatedb()
      self.run_in_thread(self.shell.updatedb, {})
      
      self.try_sem()

      if self.shell.get_prev_return() == None:
        print 'None!'
        return None
      
      ret, ret_err = self.shell.get_prev_return()
      if self.shell.get_exit_status() != 0:
        systray_tooltip_text = 'Error updating database'
        self.systray_tooltips.set_tip(self.systray_eventbox, systray_tooltip_text)
      else:
        systray_tooltip_text = 'Update(s) available'
        self.systray_tooltips.set_tip(self.systray_eventbox, systray_tooltip_text)

    #print 'setting alarm to: ', self.pkg_update_alarm
    #signal.alarm(self.pkg_update_alarm)

  # }}}

  # def on_pacman_log_activate(self, menuitem): {{{
  def on_pacman_log_activate(self, menuitem):
    if self.pacman_log_file == '':
      self.pacman_log_file = '/var/log/pacman.log'

    pacman_log = open(self.pacman_log_file, 'r')

    buffer = gtk.TextBuffer()
    #log = pacman_log.read()
    lines = pacman_log.readlines()
    start = buffer.get_start_iter()
    
    for line in lines:
      buffer.insert(start, line, len(line))
    pacman_log_dialog = self.all_widgets.get_widget('pacman_log_dialog')
    self.current_dialog = pacman_log_dialog

    pacman_log_textview = self.all_widgets.get_widget('pacman_log_textview')

    pacman_log_textview.set_buffer(buffer)

    self.current_dialog_on = True
    pacman_log_dialog.run()
    pacman_log_dialog.hide()
    self.current_dialog_on = False

  # }}}

  # def on_install_pkg_from_file_activate(self, menuitem): {{{
  def on_install_pkg_from_file_activate(self, menuitem):
    #self.liststore = gtk.ListStore('gboolean', str, str, str)

    #self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
    install_pkg_popup = self.all_widgets.get_widget('install_pkg_popup')

    pkg_filechooser_dialog =\
      self.all_widgets.get_widget('pkg_filechooser_dialog')
    self.current_dialog = pkg_filechooser_dialog
    
    filter = gtk.FileFilter()
    filter.set_name('Pacman Files')
    filter.add_pattern('*.pkg.tar.gz')

    pkg_filechooser_dialog.add_filter(filter)

    pkg_filechooser_dialog.set_current_folder('/var/cache/pacman/pkg/')
    self.current_dialog_on = True
    response = pkg_filechooser_dialog.run()

    pkg_filechooser_dialog.hide()
    self.current_dialog_on = False
    if response == gtk.RESPONSE_OK:
      #pathname = pkg_filechooser_dialog.get_filename()
      path_list = pkg_filechooser_dialog.get_filenames()
      
      install_pkg_are_you_sure_dialog =\
      self.all_widgets.get_widget('install_pkg_are_you_sure_dialog')
      self.current_dialog = install_pkg_are_you_sure_dialog

      install_are_you_sure_label =\
        self.all_widgets.get_widget('install_are_you_sure_label')
      
      label_text = ''
      pkgs = []
      for pathname in path_list:
        index = pathname.rfind('/')

        pkg = pathname[index+1:]
        pkg = pkg[:pkg.find('.')]
        pkg = pkg[:pkg.rfind('-')]

        pkgs.append(pkg)

        if label_text == '':
          label_text = pkg
        else:
          label_text = label_text + pkg + '\n'

      install_are_you_sure_label.set_text(label_text)

      self.main_window.set_sensitive(False)
      self.current_dialog_on = True
      response = install_pkg_are_you_sure_dialog.run()
      install_pkg_are_you_sure_dialog.hide()
      self.current_dialog_on = False

      if response == gtk.RESPONSE_OK:
        selection = self.treeview.get_selection()
        treemodel, iter = selection.get_selected()
        #if not iter:
        #  return

        #ret,ret_err = self.shell.install_pkg_from_file(pathname)
        self.run_in_thread(self.shell.install_pkg_from_files,
            {'path_list': path_list})

        self.try_sem_animate_progress_bar()

        if self.shell.get_prev_return() == None:
          print 'None!'
          return None
        
        ret, ret_err = self.shell.get_prev_return()
        
        if self.shell.get_exit_status() == 0:
          self.__add_pkg_info_to_local_pkgs__(pkgs)
          self.refresh_pkgs_treeview()
          
          self.current_dialog = install_pkg_popup
          self.current_dialog_on = True
          install_pkg_popup.run()
          install_pkg_popup.hide()
          self.current_dialog_on = False
          
          self.main_window.set_sensitive(True)
          #self.refresh_pkgs_treeview()
          
          #repo = 'no repository'
          #self.__fill_treeview_with_pkgs_from_repo__(repo.lower())
        else:
          #TODO: more cases can happen here
          deps = []
          if ret.index('requires'):
            # dependencies required
            dependencies_required_dialog =\
                self.all_widgets.get_widget('dependencies_required_dialog')
            self.current_dialog = dependencies_required_dialog
            dependencies_required_label =\
                self.all_widgets.get_widget('dependencies_required_label')

            pattern = 'requires\s([a-zA-Z0-9\-]*)'
            regexp = re.compile(pattern)

            iter = regexp.finditer(ret)

            for match in iter:
              string = ret[match.start()+len('requires '):match.end()]
              deps.append(string)

            label_text2 = ''

            for dep in deps:
              if label_text2 == '':
                label_text2 = dep + '\n'
              else:
                label_text2 = label_text2 + dep + '\n'

            dependencies_required_label.set_text(label_text2)

            full_path_deps = self.__expand_deps_list__(deps)

            self.current_dialog_on = True
            response_3 = dependencies_required_dialog.run()
            dependencies_required_dialog.hide()
            self.current_dialog_on = False

            if response_3 == gtk.RESPONSE_OK:
              self.run_in_thread(self.shell.install_pkg_from_files,
                  {'path_list': path_list + full_path_deps})

              self.try_sem_animate_progress_bar()

              self.__add_pkg_info_to_local_pkgs__(pkgs + deps)
              self.refresh_pkgs_treeview()

              install_pkg_popup.run()
              install_pkg_popup.hide()
              self.current_dialog_on = False
            else:
              return

          self.main_window.set_sensitive(True)
            #while (match = regexp.match(ret)):
            #  print 'dep: ', line[match]
      else:
        return 
    else:
      return 
    
  # }}}

  # def on_systray_popup_menu_show_window_activate(self, menuitem): {{{
  def on_systray_popup_menu_show_window_activate(self, menuitem):
    self.main_window_hidden = False
    self.main_window.show()
  # }}}

  # def on_systray_popup_menu_preferences_activate(self, menuitem): {{{
  def on_systray_popup_menu_preferences_activate(self, menuitem):
    self.on_preferences_clicked(None)
  # }}}

  # def on_systray_popup_menu_quit_activate(self, menuitem): {{{
  def on_systray_popup_menu_quit_activate(self, menuitem):
    self.on_quit_activate(None)
  # }}}

  # def on_systray_eventbox_button_press_event(self): {{{
  def on_systray_eventbox_button_press_event(self, widget, event):
    if event.button == 1: # left click
      
      if self.main_window_hidden:
        self.main_window.show()
        self.main_window_hidden = False
      else:
        self.main_window.hide()
        self.main_window_hidden = True
      
      if self.busy_window_on:
        if self.busy_window_hidden:
          self.busy_window.show()
          self.busy_window_hidden = False
        else:
          self.busy_window.hide()
          self.busy_window_hidden = True

      #if self.current_dialog_on:
      #  if self.current_dialog_hidden:
      #    self.current_dialog.show()
      #    self.current_dialog_hidden = False
      #  else:
      #    self.current_dialog.hide()
      #    self.current_dialog_hidden = True

    if event.button == 2: # middle click
      # do nothing?
      pass
    if event.button == 3: # right click
      # show popup menu
      systray_popup_menu = self.all_widgets.get_widget('systray_popup_menu')
      systray_popup_menu.popup(None, None, None, event.button, event.get_time())
  # }}}

  # def on_systray_eventbox_motion_notify_event(self): {{{
  def on_systray_eventbox_motion_notify_event(self, widget, event):
    #print 'systray motion notify event'
    pass
  # }}}

  # def on_systray_eventbox_leave_notify_event(self): {{{
  def on_systray_eventbox_leave_notify_event(self, widget, event):
    #print 'on_systray_eventbox_leave_notify_event'
    pass
  # }}}

  # def on_about_activate(self): {{{
  def on_about_activate(self, menuitem):
    about_dialog = self.all_widgets.get_widget('about_dialog')
    self.current_dialog = about_dialog

    self.current_dialog_on = True
    about_dialog.run()
    about_dialog.hide()
    self.current_dialog_on = False
  # }}}

  # def on_cursor_changed(self, treeview): {{{
  def on_cursor_changed(self, treeview):
    selection = treeview.get_selection()
    treemodel, iter = selection.get_selected()
    info = ''
    if not iter:
      return 

    if treeview == self.treeview:
      (tuple, column) = treeview.get_cursor()

      if not column:
        return
      renderers = column.get_cell_renderers()

      # don't show a popup if the column is a CellRendererToggle
      if type(renderers[0]) is gtk.CellRendererToggle:
        return

      # treeview of pkgs
      name = treemodel.get_value(iter, 1)

      #print 'name:<%s>' % name
      
      buffer = gtk.TextBuffer()
      
      try:
        info = self.local_pkg_info[name]
      except KeyError:
        #info = self.shell.local_info(name)
        self.run_in_thread(self.shell.local_info, {'what': name})

        self.try_sem_animate_progress_bar()

        info = self.shell.get_prev_return()
        self.local_pkg_info[name] = info
      
      if info == None:
        try:
          remote_info = self.remote_pkg_info[name]
        except KeyError:
          #remote_info = self.shell.info(name)
          self.run_in_thread(self.shell.info, {'what': name})

          self.try_sem()

          if self.shell.get_prev_return() == None:
            print 'None! CC2'
            return None
          
          remote_info = self.shell.get_prev_return()
          self.remote_pkg_info[name] = remote_info

        self.__add_pkg_info_markuped_to_text_buffer__(buffer, remote_info,\
            installed = False)
        #self.__add_pkg_info_markuped_to_pkg_info_label__(remote_info,
        #    installed = False)
      else:
        self.__add_pkg_info_markuped_to_text_buffer__(buffer, info)
        #self.__add_pkg_info_markuped_to_pkg_info_label__(info)
      self.information_text.set_buffer(buffer)
      #tag_list = self.information_text.get_buffer().\
      #    get_start_iter().get_tags()

      #for tag in tag_list:
      #  print tag.get_property('name')

    else: # treeview of repos
      repo = treemodel.get_value(iter, 0)
      if repo == 'Pseudo Repos' or repo == 'Repos':
        return 
      # fill treeview with pkgs from 'repo'
      self.__fill_treeview_with_pkgs_from_repo__(repo.lower())
  # }}}

  # def on_select_cursor_row(self, treeview, start_editing): {{{
  def on_select_cursor_row(self, treeview, start_editing):
    print treeview
    print start_editing
    print treeview.get_cursor()
  # }}}

  # def on_quit_activate(self, menuitem): {{{
  def on_quit_activate(self, menuitem):
    gobject.source_remove(self.timer)
    self.timer = 0
    gtk.main_quit()
    return False
  # }}}

  # def on_destroy(self, widget, data=None): {{{
  def on_destroy(self, widget, data=None):
    if widget == self.main_window:
      gobject.source_remove(self.timer)
      self.timer = 0
      gtk.main_quit()
      return False
    else:
      self.update_db_popup.hide()
      return False
  # }}}

  # def on_install_pkg_popup_destroy(self, widget, data=None): {{{
  def on_install_pkg_popup_destroy(self, widget, data=None):
    self.install_pkg_popup.hide()
    return False
  # }}}

  # def on_delete_event(self, widget, event, data=None): {{{
  def on_delete_event(self, widget, event, data=None):
    return False
  # }}}

  # def on_install_pkg_popup_delete_event(self, widget, event, data=None): {{{
  def on_install_pkg_popup_delete_event(self, widget, event, data=None):
    return False
  # }}}

  # def on_row_activated(self, treeview, path, column): {{{
  #def on_row_activated(self, treeview, path, column):
  #  print 'row!'
  #  print 'treeview :',treeview
  #  print 'path :',path
  #  print 'column :',column
  # }}}

  # def on_update_db_clicked(self, button, skip_update_db = False): {{{
  def on_update_db_clicked(self, button, skip_update_db = False):
    #if button == self.update_db and self.__is_root__():
    if button == self.update_db:
      #ret, ret_err = self.shell.updatedb()
      if not skip_update_db:
        self.run_in_thread(self.shell.updatedb, {})

        self.try_sem_animate_progress_bar()

        if self.shell.get_prev_return() == None:
          print 'None!'
          return None

        ret, ret_err = self.shell.get_prev_return()
        
        print 'ret: ', ret
        print 'ret_err: ',ret_err

        if self.shell.get_exit_status() != 0:
          # something has gone horribly wrong
          pacman_error_label = self.all_widgets.get_widget('pacman_error_label')
          pacman_error_dialog =\
              self.all_widgets.get_widget('pacman_error_dialog')
          self.current_dialog = pacman_error_dialog
          pacman_error_label.set_text(ret_err)
          self.current_dialog_on = True
          pacman_error_dialog.run()
          pacman_error_dialog.hide()
          self.current_dialog_on = False
          return 

        self.update_db_popup = self.all_widgets.get_widget('update_db_popup')
        self.current_dialog = self.update_db_popup
        self.current_dialog_on = True
        response = self.update_db_popup.run()

        self.update_db_popup.hide()
        self.current_dialog_on = False

      #updates = self.shell.get_fresh_updates()
      #self.run_in_thread(self.shell.get_fresh_updates, {})
      self.run_in_thread(self.shell.get_fresh_updates_part_1, {})

      self.try_sem_animate_progress_bar()

      if self.shell.get_prev_return() == None:
        print 'None!'
        return None
      
      (yesno, out, err) = self.shell.get_prev_return()
      
      if err:
        pacman_error_dialog =\
            self.all_widgets.get_widget('pacman_error_dialog')
        self.current_dialog = pacman_error_dialog
        pacman_error_label = self.all_widgets.get_widget('pacman_error_label')
        pacman_error_label.set_text(err)
        self.current_dialog_on = True
        pacman_error_dialog.run()
        pacman_error_dialog.hide()
        self.current_dialog_on = False
        return

      try:
        out.index('Upgrade pacman first?')
        # this means there's a new version of pacman to upgrade
        # to upgrade it
        pacman_upgrade_dialog =\
          self.all_widgets.get_widget('pacman_upgrade_dialog')
        self.current_dialog = pacman_upgrade_dialog
        
        self.current_dialog_on = True
        response = pacman_upgrade_dialog.run()
        pacman_upgrade_dialog.hide()
        self.current_dialog_on = False
        
        if response == gtk.RESPONSE_OK:
          self.run_in_thread(self.shell.get_fresh_updates_part_2,
              {'pacman_upgrade': True, 'out': out})
          self.install_packages_from_list(['pacman'])

          self.try_sem_animate_progress_bar()

          self.on_update_db_clicked(button, True)
          
        else:
          self.run_in_thread(self.shell.get_fresh_updates_part_2,
              {'pacman_upgrade': True, 'out': out})
          self.try_sem_animate_progress_bar()
      except ValueError:
        self.run_in_thread(self.shell.get_fresh_updates_part_2,
            {'pacman_upgrade': False, 'out': out})
        self.try_sem_animate_progress_bar()
        
      updates, out = self.shell.get_prev_return()

      if updates == None: # conflicts
        #lines = out.splitlines()
        try:
          index = out.index('conflicts')
          tmp = out[:index].strip()
          index2 = tmp.rfind(' ')
          conflicting_pkg = tmp[index2:].strip()
          tmp = out[index:]
          conflict_pkg = tmp[tmp.index('with')+1+len('with') : tmp.index('.')].strip()

          generic_cancel_ok = self.all_widgets.get_widget('generic_cancel_ok')
          generic_cancel_ok_label =\
              self.all_widgets.get_widget('generic_cancel_ok_label')
          generic_cancel_ok_label.set_markup('<b>Warning</b>\n\n' +
              out[3:out.rindex('.')] +\
            '\n\nDo you wish to proceed?')
          
          self.current_dialog_on = True
          response3 = generic_cancel_ok.run()
          generic_cancel_ok.hide()
          self.current_dialog_on = False

          if response3 == gtk.RESPONSE_OK:
            self.run_in_thread(self.shell.install_noconfirm, {'what':\
                conflicting_pkg})
            self.try_sem_animate_progress_bar()
        
            self.shell.yesno = False
            self.run_in_thread(self.shell.get_fresh_updates_part_2,
                {'pacman_upgrade': False, 'out': out})
            self.try_sem_animate_progress_bar()

            updates, out = self.shell.get_prev_return()
          else:
            return
        except ValueError:
          pass
        return
      
      if updates == []:
        no_updates_dialog = self.all_widgets.get_widget('no_updates_dialog')
        self.current_dialog = no_updates_dialog
        self.current_dialog_on = True
        no_updates_dialog.run()
        no_updates_dialog.hide()
        self.current_dialog_on = False
        return 

      fresh_updates_dialog = self.all_widgets.get_widget('fresh_updates_dialog')
      self.current_dialog = fresh_updates_dialog
      fresh_updates_label = self.all_widgets.get_widget('fresh_updates_label')

      updates_text = 'Targets:'
      for update in updates:
        updates_text = updates_text + '\n' + update

      fresh_updates_label.set_text(updates_text)

      self.current_dialog_on = True
      response = fresh_updates_dialog.run()
      fresh_updates_dialog.hide()
      self.current_dialog_on = False
      
      fresh_updates_installed = False
      
      if response == gtk.RESPONSE_OK:
        #self.shell.install_fresh_updates()
        self.run_in_thread(self.shell.install_fresh_updates, {})
        self.try_sem_animate_progress_bar()
        fresh_updates_installed = True  
      else:
        return

      # TODO: is this necessary?
      for pkg_name in updates:
        #info = self.shell.info(pkg_name)
        self.run_in_thread(self.shell.info, {'what':pkg_name})

        self.try_sem()
        if self.shell.get_prev_return() == None:
          print 'None!'
          return None
        
        info = self.shell.get_prev_return()
        #self.local_pkg_info[pkg_name] = info
        self.remote_pkg_info[pkg_name] = info
      
      if fresh_updates_installed:
        self.__add_pkg_info_to_local_pkgs__(updates)
        
        pkgs_updated_dialog = self.all_widgets.get_widget('pkgs_updated_dialog')
        self.current_dialog = pkgs_updated_dialog
        pkgs_updated_label = self.all_widgets.get_widget('pkgs_updated_label')
        pkgs_updated_label.set_text(updates_text)

        self.current_dialog_on = True
        pkgs_updated_dialog.run()
        pkgs_updated_dialog.hide()
        self.current_dialog_on = False
    else:
      # display a warning window?? switch to root?? gksu???
      print 'not root!'
  # }}}

  # def on_okbutton_clicked(self, button): {{{
  def on_okbutton_clicked(self, button):
    self.update_db_popup.hide()
  # }}}

  # def on_okbutton2_clicked(self, button): {{{
  def on_okbutton2_clicked(self, button):
    self.install_pkg_popup.hide()
  # }}}

  # def on_install_pkg_clicked(self, button): {{{
  def on_install_pkg_clicked(self, button):
    pkgs_to_install = self.get_all_selected_packages(self.liststore)

    if pkgs_to_install == []:
      return 
    
    self.install_packages_from_list(pkgs_to_install)
  # }}}

  # def on_remove_pkg_clicked(self, button): {{{
  def on_remove_pkg_clicked(self, button):
    pkgs_to_remove = self.get_all_selected_packages(self.liststore)

    if pkgs_to_remove == []:
      return 
    self.remove_packages_from_list(pkgs_to_remove)
  # }}}

  # def on_install_from_repo_button_clicked(self, button): {{{
  def on_install_from_repo_button_clicked(self, button):
    # TODO: WARNING: To test this I have to use 'testing' repo :|
    repo_choice_dialog = self.all_widgets.get_widget('repo_choice_dialog')
    self.current_dialog = repo_choice_dialog
    repo_choice_combobox = self.all_widgets.get_widget('repo_choice_combobox')

    repo_liststore = gtk.ListStore(str)
    
    for repo in sorted(self.pkgs_by_repo.keys()):
      #repo_choice_combobox.append_text(repo)
      repo_liststore.append([repo])

    repo_choice_combobox.set_model(repo_liststore)
    
    cell = gtk.CellRendererText()
    repo_choice_combobox.pack_start(cell, True)
    repo_choice_combobox.add_attribute(cell, 'text', 0)  
    
    repo_choice_combobox.set_active(0)

    self.current_dialog_on = True
    response = repo_choice_dialog.run()
    repo_choice_dialog.hide()
    self.current_dialog_on = False

    if response == gtk.RESPONSE_OK:
      repo_to_use = repo_choice_combobox.get_active_text()
      
      pkgs_to_install = self.get_all_selected_packages(self.liststore)

      if pkgs_to_install == []:
        return 
    
      self.install_packages_from_list(pkgs_to_install, repo_to_use)
    else:
      return
  # }}}

  # def on_update_db_popup_delete_event(self, widget, event, data=None): {{{
  def on_update_db_popup_delete_event(self, widget, event, data=None):
    self.update_db_popup.hide()
    self.update_db_popup.destroy()
  # }}}

  # def on_search_clicked(self, button): {{{
  def on_search_clicked(self, button):
    self.liststore = gtk.ListStore('gboolean', str, str, str)

    try:
      regexp = re.compile(self.search_entry.get_text())
    except sre_constants.error:
      pass
    search_combobox = self.all_widgets.get_widget('search_combobox')
    # search current, extra, community
    # self.pkgs_by_repo: dict of repos with lists of pairs with
    # (name, version)
    # TODO: use search_combobox.get_active() instead of get_active_text()?? 
    #       better for i18n? cleaner?
    # TODO: search in remote_pkg_info ??
    where_to_search = search_combobox.get_active_text()
    
    if where_to_search != None:
      for repo, repo_list in self.pkgs_by_repo.iteritems():
        #for pkg_info in repo_list:
        for name, version, description in repo_list:
          if where_to_search == 'Version':
            match = regexp.match(version)
          elif where_to_search == 'Name':
            match = regexp.match(name)
          else: # description
            match = regexp.match(description)
          if match:
            try:
              installed_version = self.local_pkgs[name][1]
            except KeyError:
              installed_version = '--'
            self.liststore.append([False, name, installed_version, version])
          
      self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
      self.treeview.set_model(self.liststore)
    else: # this should not happed but it stays here for completeness
      no_search_selected_dialog =\
        self.all_widgets.get_widget('no_search_selected_dialog')
      self.current_dialog = no_search_selected_dialog
      self.current_dialog_on = True
      no_search_selected_dialog.run()
      no_search_selected_dialog.hide()
      self.current_dialog_on = False
  # }}}

  # def on_clear_clicked(self, button): {{{
  def on_clear_clicked(self, button):
    # clear the search_entry
    self.search_entry.set_text('')

    # set the pkg treemodel to whatever repo is selected in the repo treeview
    # TODO: is this necessary?
    selection = self.treeview_repos.get_selection()
    treemodel, iter = selection.get_selected()

    if not iter:
      return 
    else:
      self.refresh_pkgs_treeview()
  # }}}

  # def on_treeview_button_press_event(self, treeview, event): {{{
  def on_treeview_button_press_event(self, treeview, event):
    if event.button == 3:
      # display popup menu
      x = int(event.x)
      y = int(event.y)
      pathinfo = treeview.get_path_at_pos(x, y)
      if pathinfo != None:
        path, col, cellx, celly = pathinfo
        treeview.set_cursor(path, col, 0)

      popup_menu = self.all_widgets.get_widget('popup_menu')

      popup_menu.popup(None, None, None, event.button, event.get_time())
      return True
  # }}}

  # def on_install_popup_menu_activate(self, menuitem): {{{
  def on_install_popup_menu_activate(self, menuitem):
    selection = self.treeview.get_selection()
    treemodel, iter = selection.get_selected()
    if not iter:
      return 

    name = treemodel.get_value(iter, 1)
    pkgs_to_install = [name]
    self.install_packages_from_list(pkgs_to_install)
  # }}}

  # def on_install_from_popup_menu_activate(self, menuitem): {{{
  def on_install_from_popup_menu_activate(self, menuitem):
    # TODO: WARNING: To test this I have to use 'testing' repo :|
    repo_choice_dialog = self.all_widgets.get_widget('repo_choice_dialog')
    self.current_dialog = repo_choice_dialog
    repo_choice_combobox = self.all_widgets.get_widget('repo_choice_combobox')

    repo_liststore = gtk.ListStore(str)
    
    for repo in sorted(self.pkgs_by_repo.keys()):
      #repo_choice_combobox.append_text(repo)
      repo_liststore.append([repo])

    repo_choice_combobox.set_model(repo_liststore)
    
    cell = gtk.CellRendererText()
    repo_choice_combobox.pack_start(cell, True)
    repo_choice_combobox.add_attribute(cell, 'text', 0)  
    
    repo_choice_combobox.set_active(0)

    self.current_dialog_on = True
    response = repo_choice_dialog.run()
    repo_choice_dialog.hide()
    self.current_dialog_on = False

    if response == gtk.RESPONSE_OK:
      repo_to_use = repo_choice_combobox.get_active_text()

      selection = self.treeview.get_selection()
      treemodel, iter = selection.get_selected()
      if not iter:
        return 

      name = treemodel.get_value(iter, 1)
      pkgs_to_install = [name]
      self.install_packages_from_list(pkgs_to_install, repo_to_use)
    else:
      return
  # }}}

  # def on_remove_popup_menu_activate(self): {{{
  def on_remove_popup_menu_activate(self, menuitem):
    selection = self.treeview.get_selection()
    treemodel, iter = selection.get_selected()
    if not iter:
      return 

    name = treemodel.get_value(iter, 1)
    pkgs_to_remove = [name]
    self.remove_packages_from_list(pkgs_to_remove)
  # }}}

  # def on_view_files_popup_menu_activate(self, menuitem): {{{
  def on_view_files_popup_menu_activate(self, menuitem):
    selection = self.treeview.get_selection()
    treemodel, iter = selection.get_selected()
    if not iter:
      return 

    name = treemodel.get_value(iter, 1)
    
    pkg_files_dialog = self.all_widgets.get_widget('pkg_files_dialog')

    pkg_files_textview = self.all_widgets.get_widget('pkg_files_textview')
    
    #buffer = pkg_files_textview.get_buffer()
    buffer = gtk.TextBuffer()
    pkg_files_textview.set_buffer(buffer)

    self.run_in_thread(self.shell.get_pkg_files, {'what': name})
    self.try_sem()
    
    exit_status, text = self.shell.get_prev_return()

    if exit_status:
      return
    buffer.insert_at_cursor(text)

    self.current_dialog = pkg_files_dialog
    pkg_files_dialog.run()
    pkg_files_dialog.hide()
    self.current_dialog_on = False
  # }}}

  # def on_mainwindow_enter_notify_event(self, widget, event): {{{
  def on_mainwindow_enter_notify_event(self, widget, event):
    print 'entered main window...'
    print widget, event
  # }}}
    
  # def on_mainwindow_motion_notify_event(self, widget, event, data = None): {{{
  def on_mainwindow_motion_notify_event(self, widget, event, data = None):
    print 'main_window!'
    #x, y, mods = self.main_window.get_pointer()

    #x, y = self.information_text.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT, x, y)
    #iter = self.information_text.get_iter_at_location(x, y)
    #buffer = iter.get_buffer()
    tag_table = self.information_text.get_buffer().get_tag_table()
    hyperlink_tag = tag_table.lookup('hyperlink')

    if hyperlink_tag == None:
      print 'main_window None!!'
      return 
    
    hyperlink_tag.set_property('underline', self.pango_no_underline)
    self.information_text.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(None)
  # }}}
  
  # def on_hyperlink_motion(self, widget, event, data = None): {{{
  def on_hyperlink_motion(self, widget, event, data = None):
    #x, y, mods = self.main_window.get_pointer()

    #x, y = self.information_text.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT, x, y)
    #iter = self.information_text.get_iter_at_location(x, y)
    #buffer = iter.get_buffer()
    #tags = iter.get_tags()
    tag_table = self.information_text.get_buffer().get_tag_table()
    hyperlink_tag = tag_table.lookup('hyperlink')

    if hyperlink_tag == None:
      print 'hyperlink None!!'
      return 
    
    hyperlink_tag.set_property('underline', self.pango_underline_single)
    #self.information_text.get_window(gtk.TEXT_WINDOW_TEXT)\
    #    .set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND))
    self.underlined_url = hyperlink_tag

  # }}}

  # def on_hyperlink_clicked(self, tag, widget, event, iter, link): {{{
  def on_hyperlink_clicked(self, tag, widget, event, iter, link):
    thread.start_new_thread(os.popen, (self.browser + ' ' + link, 'r'))
  # }}}

  # def on_cache_menu_activate(self, menuitem): {{{
  def on_cache_menu_activate(self, menuitem):
    #cache_dialog = self.all_widgets.get_widget('cache_dialog')
    cache_dialog = self.all_widgets.get_widget('cache_dialog2')
    self.current_dialog = cache_dialog

    #cache_treeview = self.all_widgets.get_widget('cache_treeview')
    cache_treeview = self.all_widgets.get_widget('cache_treeview2')

    cache_liststore = gtk.TreeStore(str, str)
    
    textrenderer = gtk.CellRendererText()

    pkg_cache_name_column = gtk.TreeViewColumn('Name')
    pkg_cache_name_column.set_sort_column_id(0)
    pkg_cache_name_column.pack_start(textrenderer)
    pkg_cache_name_column.set_attributes(textrenderer, text=0)


    pkg_cache_version_column = gtk.TreeViewColumn('Version')
    pkg_cache_version_column.set_sort_column_id(1)
    pkg_cache_version_column.pack_start(textrenderer)
    pkg_cache_version_column.set_attributes(textrenderer, text=1)

    pkg_cache_days_column = gtk.TreeViewColumn('Days')
    pkg_cache_days_column.set_sort_column_id(2)
    pkg_cache_days_column.pack_start(textrenderer)
    pkg_cache_days_column.set_attributes(textrenderer, text=2)

    cache_treeview.append_column(pkg_cache_name_column)
    cache_treeview.append_column(pkg_cache_version_column)
    #cache_treeview.append_column(pkg_cache_days_column)
    
    cache_pkgs = self.get_cache_pkgs()

    self.already_seen = {}
    self.pkg_versions = {}
    
    for package in cache_pkgs:
      # strip '.pkg.tar.gz'
      index = package.index('.pkg.tar.gz')
      tmp = package[:index]
      #version_index = tmp[:tmp.rindex('-')].rindex('-')
      #pkg_name = tmp[:version_index]
      #pkg_version = tmp[version_index+1:]
      pkg_name, pkg_version = self.split_pkg_name(tmp)
      
      try:
        iter_old = self.already_seen[pkg_name]
        self.pkg_versions[pkg_name]
        cache_liststore.append(iter_old, [pkg_name, pkg_version])
      except KeyError:
        iter = cache_liststore.append(None, [pkg_name, None])
        cache_liststore.append(iter, [pkg_name, pkg_version])
        self.already_seen[pkg_name] = iter

      try:
        self.pkg_versions[pkg_name].append(pkg_version)
      except KeyError:
        self.pkg_versions[pkg_name] = [pkg_version]

    cache_treeview.set_model(cache_liststore)

    #print self.pkg_versions

    self.current_dialog_on = True
    response = cache_dialog.run()

    if response == gtk.RESPONSE_YES:
      # cleanup cache
      cache_combobox = self.all_widgets.get_widget('cache_combobox')
      clean_by = cache_combobox.get_active_text()
      cache_spinbutton = self.all_widgets.get_widget('cache_spinbutton')
      clean_threshold = cache_spinbutton.get_value_as_int()
      self.cleanup_cache(clean_by, clean_threshold)
    else:
      pass
    cache_dialog.hide()
    self.current_dialog_on = False
  # }}}

  # def on_busy_cancel_button_clicked(self, button): {{{
  def on_busy_cancel_button_clicked(self, button):
    print 'killing...'
    #os.kill(self.shell.get_pid(), signal.SIGKILL) 
    #self.stop_pulsing = True
    self.lock.acquire()
    print 'self.th: ', self.th
    #while self.th.isAlive() == True:
    #  print 'bump'
    #  while gtk.events_pending():
    #    gtk.main_iteration(False)
    #  self.th.join(0.1)
  # }}}

  # def cleanup_cache(self, clean_by, clean_threshold): {{{
  def cleanup_cache(self, clean_by, clean_threshold):
    cache_dir = '/var/cache/pacman/pkg'
    time_now = time.time()
    print 'now is: ', int(time_now)
    
    already_cleaned = {}
    cleaned = []
    for package in sorted(os.listdir(cache_dir)):
      index = package.index('.pkg.tar.gz')
      tmp = package[:index]
      pkg_name, pkg_version = self.split_pkg_name(tmp)

      if not os.path.isdir(os.path.join(cache_dir, package)):
        # do the cleanup
        path = os.path.join(cache_dir, package)

        if clean_by == 'Days':
          # cleanup by days {{{
          mtime = os.stat(path).st_mtime
          clean_secs = clean_threshold * 24 * 60 * 60
          if time_now - mtime >= clean_secs:
            length = len(self.pkg_versions[pkg_name])
            if length > 1:
              # more than one version
              if self.pkg_versions[pkg_name][length-1] != pkg_version:
                # not trying to clean the last version
                #print 'removing: ', path
                del self.pkg_versions[pkg_name][0]
                cleaned.add(path)
                os.remove(path)
              else:
                print 'trying to clean the last version: ',\
                  ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
            else:
              print 'there is only one version in cache: ',\
                  ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
          # }}}
        else:
          # cleanup by version {{{
          length = len(self.pkg_versions[pkg_name])
          if length > clean_threshold:
            #print 'removing: ', path
            i = 0
            while i < clean_threshold:
              del self.pkg_versions[pkg_name][0]
              i = i + 1
            cleaned.add(path)
            os.remove(path)
          else:
            #print 'there are only ', length
            #print 'versions in cache: ',\
            #    ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
            pass
          # }}}
    print 'pkgs cleaned: ', cleaned
  # }}}

  # def split_pkg_name(self, pkg_name): {{{
  def split_pkg_name(self, pkg_name):
    if pkg_name == '':
      return None
    version_index = pkg_name[:pkg_name.rindex('-')].rindex('-')
    pkg_name2 = pkg_name[:version_index]
    pkg_version = pkg_name[version_index+1:]
    return pkg_name2, pkg_version
  # }}}
  
  # def get_pkg_name(self, pkg_name): {{{
  def get_pkg_name(self, pkg_name):
    if pkg_name == '':
      return None
    version_index = pkg_name[:pkg_name.rindex('-')].rindex('-')
    pkg_name2 = pkg_name[:version_index]
    #pkg_version = pkg_name[version_index+1:]
    return pkg_name2
  # }}}

  # def get_cache_pkgs(self): {{{
  def get_cache_pkgs(self):
    cache_dir = '/var/cache/pacman/pkg'

    ret = []
    
    for pkg_name in sorted(os.listdir(cache_dir)):
      if not os.path.isdir(os.path.join(cache_dir, pkg_name)):
        ret.append(pkg_name)
    return ret
  # }}}

  # def write_conf(self): {{{
  def write_conf(self):
    # write self.pkg_update_alarm
    conf_filename = os.environ['HOME'] + '/.guzutarc'
    try:
      conf_file = open(conf_filename, 'w')
    except IOError:
      print 'Failure to open %s for writing. Bailing out' % conf_filename
      return
    #conf_file.write('pkg_update_alarm = ' + str(self.pkg_update_alarm) + '\n')
    #conf_file.write('pkg_update_alarm_period = ' +\
    #    str(self.pkg_update_alarm_period) + '\n')
    conf_file.write('pacman_log_file = ' + self.pacman_log_file + '\n')
    conf_file.write('browser = ' + self.browser + '\n')
    conf_file.close()
  # }}}

  # def read_conf(self): {{{
  def read_conf(self):
    conf_filename = os.environ['HOME'] + '/.guzutarc'
    try:
      conf_file = open(conf_filename, 'r')
    except IOError:
      return
    contents = conf_file.readlines()

    use_default = False
    
    for line in contents:
      if line.startswith('pkg_update_alarm ='):
        #TODO: implement when auto update works. alarm is giving a keyboarderror
        #      ???
        #equal_pos = line.index('=')
        #self.pkg_update_alarm = int(line[equal_pos+1:].strip())
        #if self.pkg_update_alarm == 0:
        #  self.pkg_update_alarm = 2
        #  use_default = True
        pass
      elif line.startswith('pacman_log_file ='):
        equal_pos = line.index('=')
        self.pacman_log_file = line[equal_pos+1:].strip()
      elif line.startswith('browser ='):
        equal_pos = line.index('=')
        self.browser = line[equal_pos+1:].strip()
      elif line.startswith('pkg_update_alarm_period ='):
        #TODO: implement when auto update works. alarm is giving a keyboarderror
        #      ???
        #if use_default:
        #  self.pkg_update_alarm_period = 1
        #else:
        #  equal_pos = line.index('=')
        #  self.pkg_update_alarm_period = int(line[equal_pos+1:].strip())
        #  if self.pkg_update_alarm_period <0 or self.pkg_update_alarm_period>1:
        #      self.pkg_update_alarm_period = 1
        #      use_default = True
        pass
  # }}}
  
  # def download_packages(self, pkg_list): {{{
  def download_packages(self, pkg_list):
    what = ''
    pkg_names_by_comma = ''

    for pkg_name in pkg_list:
      what = what + pkg_name + ' '

    self.run_in_thread(self.shell.download_part_1, {'what': what})
    self.try_sem_animate_progress_bar()

    if self.shell.get_prev_return() == None:
      print 'None'
      return

    out = self.shell.get_prev_return()
    exit_status = self.shell.get_exit_status()

    if exit_status == 0:
      download_pkgs_dialog = self.all_widgets.get_widget('download_pkgs_dialog')
      self.current_dialog = download_pkgs_dialog
      download_pkgs_label =\
        self.all_widgets.get_widget('download_pkgs_label')
      download_pkgs_label.set_text(out[:-7])

      self.current_dialog_on = True
      response = download_pkgs_dialog.run()
      download_pkgs_dialog.hide()
      self.current_dialog_on = False

      if response == gtk.RESPONSE_OK:
        self.run_in_thread(self.shell.download_part_2, {'txt_to_pacman': 'Y'})
        self.try_sem_animate_progress_bar()
        return (True, out)
      else:
        self.run_in_thread(self.shell.download_part_2, {'txt_to_pacman': 'n'})
        self.try_sem_animate_progress_bar()
        return (False, out)
  # }}}

  # def download_packages_from_list(self, list): {{{
  def download_packages_from_list(self, list):
    downloaded_pkgs_dialog =\
        self.all_widgets.get_widget('downloaded_pkgs_dialog')
    self.current_dialog = downloaded_pkgs_dialog

    downloaded_pkgs_label =\
        self.all_widgets.get_widget('downloaded_pkgs_label')


    (retcode, output) = self.download_packages(list)

    if retcode == False:
      return
    txt = ''
    for pkg_name in list:
      if txt == '':
        txt = pkg_name + '\n'
      else:
        txt = txt + pkg_name + '\n'

    downloaded_pkgs_label.set_text(txt)

    self.current_dialog_on = True
    downloaded_pkgs_dialog.run()
    downloaded_pkgs_dialog.hide()
    self.current_dialog_on = False
  # }}}
  
  # def get_dependencies(self, pkgs_installed, output): {{{
  def get_dependencies(self, pkgs_installed, output):
    output_list = output.splitlines()
    deps_list = []
    for line in output_list:
      if line.startswith('Targets'):
        #deps_list = [self.split_pkg_name(x) for x in (line.split(' ')[1:])]
        deps_list = [self.get_pkg_name(x) for x in (line.split(' ')[1:])]
        break
    deps_list2 = []
    for dep_name in deps_list:
      if dep_name not in pkgs_installed:
        deps_list2.append(dep_name)
    return deps_list2
  # }}}

  # def install_packages(self, pkg_list, repo = ''): {{{
  def install_packages(self, pkg_list, repo = ''):
    what = ''
    pkg_names_by_comma = ''

    for pkg_name in pkg_list:
      what = what + pkg_name + ' '
      if pkg_names_by_comma == '':
        # first
        pkg_names_by_comma = pkg_name
      else:
        pkg_names_by_comma = pkg_names_by_comma + ', ' + pkg_name
    
    #(ret, output) = self.shell.install_part_1(what)
    self.run_in_thread(self.shell.install_part_1, {'what': what, 'repo': repo})
    self.try_sem_animate_progress_bar()
    if self.shell.get_prev_return() == None:
      print 'None!'
      return None
    
    (ret, output) = self.shell.get_prev_return()
    
    deps = self.get_dependencies(pkg_list, output)

    #print 'output1: ', output
    #print 'ret: ', ret

    if ret:
      # is/are already up to date, get confirmation from user about forcing the
      # install of the package
      
      install_pkg_error = self.all_widgets.get_widget('install_pkg_error')
      self.current_dialog = install_pkg_error
      install_pkg_error_label =\
        self.all_widgets.get_widget('install_pkg_error_label')
      #install_pkg_error_label.set_use_markup(True)
      text = '''<span weight="bold">Package(s) %s is(are) up to date.</span>
<span weight="bold">Upgrade anyway?</span>''' % pkg_names_by_comma
      install_pkg_error_label.set_markup(text)
      self.current_dialog_on = True
      response2 = install_pkg_error.run()

      install_pkg_error.hide()
      self.current_dialog_on = False
      if response2 == gtk.RESPONSE_CANCEL:
        return (False, output, deps)
      elif response2 == gtk.RESPONSE_OK:
        return (True, output, deps)
    else:
      # not installed, install
      return (None, output, deps)
    #return ret

    #retcode_dict = {}
    #for pkg_name in pkg_list:
    #  ret = self.shell.install(pkg_name)
    #  if self.yesno:
    #    #self.shell.send_to_pacman
    #    pass
    #  retcode_dict[pkg_name] = ret

  # }}}

  # def install_packages_from_list(self, list, repo = ''): {{{
  def install_packages_from_list(self, list, repo = ''):
    #print 'installing: '
    #for i in list:
    #  print i
    self.install_pkg_popup = self.all_widgets.get_widget('install_pkg_popup')
    (retcode, output, deps) = self.install_packages(list, repo)

    #print 'retcode: ', retcode
    # TODO: do the same for remove pkg, add 'Are you sure?' dialog to remove
    if retcode == False:
      # cancel
      #(exit_status, out) = self.shell.install_part_3('n')
      self.run_in_thread(self.shell.install_part_3, {'txt_to_pacman': 'n'})
      self.try_sem_animate_progress_bar()
      if self.shell.get_prev_return() == None:
        print 'None!'
        return None
      
      (exit_status, out) = self.get_prev_return()
      print 'retcode was False, bailing now with exit_status: ',\
        exit_status, out
      return
    elif retcode == True:
      # force upgrade 
      #exit_status = self.shell.install_packages_noconfirm(pkgs_to_install)
      #out = self.shell.install_part_2('Y')
      self.run_in_thread(self.shell.install_part_2, {'txt_to_pacman': 'Y'})
      self.try_sem_animate_progress_bar()
      if self.shell.get_prev_return() == None:
        print 'None!'
        return None
      
      out = self.shell.get_prev_return()
      #(exit_status, out) = self.shell.install_part_3('Y')
      self.run_in_thread(self.shell.install_part_3, {'txt_to_pacman': 'Y'})
      self.try_sem_animate_progress_bar()
      if self.shell.get_prev_return() == None:
        print 'None!'
        return None
      
      (exit_status, out) = self.get_prev_return()
      self.__add_pkg_info_to_local_pkgs__(list)
      self.refresh_pkgs_treeview()
      # TODO: check for proper pkg install, check for file conflicts, etc. Build
      # another popup
      print 'retcode was True, bailing now with exit_status: ', exit_status
      return
    else:
      # display generic_cancel_ok, all went well, prompt user for action
      generic_cancel_ok = self.all_widgets.get_widget('generic_cancel_ok')
      self.current_dialog = generic_cancel_ok

      generic_cancel_ok_label =\
        self.all_widgets.get_widget('generic_cancel_ok_label')

      text = '''<span weight="bold">Warning</span>
%s''' % output[:-7]

      generic_cancel_ok_label.set_markup(text)
      self.current_dialog_on = True
      response3 = generic_cancel_ok.run()

      generic_cancel_ok.hide()
      self.current_dialog_on = False
      
      if response3 == gtk.RESPONSE_OK: 
        #self.shell.install_part_2('Y')
        self.run_in_thread(self.shell.install_part_2, {'txt_to_pacman': 'Y',
            'wait': True})
        self.try_sem_animate_progress_bar()

        (out, exit_status) = self.shell.get_prev_return()

        #print 'exit_status: ', exit_status
        #print 'out3: ', out

        if exit_status:
          generic_error_dialog =\
            self.all_widgets.get_widget('generic_error_dialog')
          self.current_dialog = generic_error_dialog
          generic_error_label =\
            self.all_widgets.get_widget('generic_error_label')
          
          generic_error_label.set_text(out)

          self.current_dialog_on = True
          response = generic_error_dialog.run()
          generic_error_dialog.hide()
          self.current_dialog_on = False

          if response == gtk.RESPONSE_OK:
            #force
            self.run_in_thread(self.shell.install_force_noconfirm,\
                {'list': list})
            self.try_sem_animate_progress_bar()
          elif response == gtk.RESPONSE_CANCEL:
            return
        
        self.current_dialog = self.install_pkg_popup
        self.current_dialog_on = True
        response = self.install_pkg_popup.run()
        # TODO: do this for the dependencies to.
        #       replace list with list + deps or something like that.
        #self.__add_pkg_info_to_local_pkgs__(list)
        self.__add_pkg_info_to_local_pkgs__(list + deps)
        self.refresh_pkgs_treeview()

      elif response3 == gtk.RESPONSE_CANCEL:
        #self.shell.install_part_2('n')
        self.run_in_thread(self.shell.install_part_2, {'txt_to_pacman': 'n'})
        self.try_sem_animate_progress_bar()

      self.install_pkg_popup.hide()
      self.current_dialog_on = False

    #self.install_pkg_popup.hide()
  # }}}

  # def remove_packages_from_list(self, list): {{{
  def remove_packages_from_list(self, list):
    remove_pkg_are_you_sure =\
      self.all_widgets.get_widget('remove_pkg_are_you_sure')
    self.current_dialog = remove_pkg_are_you_sure

    are_you_sure_label = self.all_widgets.get_widget('are_you_sure_label')

    #text = 'Are you sure you want to remove the following packages?\n'
    text = ''

    for pkg_name in list:
      text = text + pkg_name + '\n'

    are_you_sure_label.set_text(text)
    self.current_dialog_on = True
    response = remove_pkg_are_you_sure.run()
    remove_pkg_are_you_sure.hide()
    self.current_dialog_on = False

    if response == gtk.RESPONSE_CANCEL:
      return
    else:
      (exit_status, dependencies, out) =\
        self.remove_packages(list)

      if exit_status != 0:
        # error ocurred
        self.remove_pkg_error = self.all_widgets.get_widget('remove_pkg_error')
        self.current_dialog = self.remove_pkg_error
        self.remove_dependencies_broken =\
          self.all_widgets.get_widget('remove_dependencies_broken')
       
        self.remove_dependencies_broken.set_text(out.rstrip())
        self.current_dialog_on = True
        response = self.remove_pkg_error.run()
        self.remove_pkg_error.hide()
        self.current_dialog_on = False
      else:
        self.remove_pkg_popup = self.all_widgets.get_widget('remove_pkg_popup')
        self.current_dialog = self.remove_pkg_popup
        self.current_dialog_on = True
        response = self.remove_pkg_popup.run()

        if response == gtk.RESPONSE_OK:
          # force
          pass
        self.remove_pkg_popup.hide()
        self.current_dialog_on = False

        # for removed_pkg in list: {{{
        for removed_pkg in list:
          # unset self.local_pkg_info and self.local_pkgs
          try:
            del self.local_pkg_info[removed_pkg]
            del self.local_pkgs[removed_pkg]
          except KeyError:
            pass
        # }}}

        self.refresh_pkgs_treeview()
  # }}}

  # def __build_trayicon__(self): {{{
  def __build_trayicon__(self):
    #self.trayicon = egg.trayicon.TrayIcon('Tray!')
    self.trayicon = trayicon.TrayIcon('Tray!')

    self.systray_eventbox = gtk.EventBox()

    self.systray_eventbox.set_visible_window(False)
    self.systray_eventbox.set_events(gtk.gdk.POINTER_MOTION_MASK)

    self.systray_eventbox.connect('button_press_event',\
        self.on_systray_eventbox_button_press_event)
    self.systray_eventbox.connect('motion_notify_event',\
        self.on_systray_eventbox_motion_notify_event)
    self.systray_eventbox.connect('leave_notify_event',\
        self.on_systray_eventbox_leave_notify_event)
    #systray_tooltip_text = "No Updates Available."
    systray_tooltip_text = "Guzuta"
    self.systray_tooltips.set_tip(self.systray_eventbox, systray_tooltip_text)
    
    img = gtk.Image()
    #img.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_MENU)
    try:
      pixbuf =\
        gtk.gdk.pixbuf_new_from_file(self.cwd + \
          '/share/guzuta/guzuta_icon_transparent.png')
    except gobject.GError:
      try:
        pixbuf =\
            gtk.gdk.pixbuf_new_from_file(\
              '/usr/share/guzuta/guzuta_icon_transparent.png'\
            )
      except gobject.GError:
        print 'systray icon not found, bailing out'
        sys.exit(1)
    img.set_from_pixbuf(pixbuf)
    self.systray_eventbox.add(img)
    
    self.trayicon.add(self.systray_eventbox)
  # }}}

  # def __disable_all_root_widgets__(self): {{{
  def __disable_all_root_widgets__(self):
    self.all_widgets.get_widget('update_db').set_sensitive(False)
    self.all_widgets.get_widget('install_pkg').set_sensitive(False)
    self.all_widgets.get_widget('remove_pkg').set_sensitive(False)
    self.all_widgets.get_widget('cache_combobox').set_sensitive(False)
    self.all_widgets.get_widget('cache_spinbutton').set_sensitive(False)
    self.all_widgets.get_widget('cache_cleanup_label').set_sensitive(False)
    self.all_widgets.get_widget('download_pkg_button').set_sensitive(False)
    self.all_widgets.get_widget('cleanup_cache_button').set_sensitive(False)
    self.all_widgets.get_widget('install_pkg_from_file').set_sensitive(False)
    self.all_widgets.get_widget('install_from_repo_button').set_sensitive(False)
    self.all_widgets.get_widget('install_pkg_from_file_button').set_sensitive(False)
    self.all_widgets.get_widget('install_popup_menu').set_sensitive(False)
    self.all_widgets.get_widget('install_from_popup_menu').set_sensitive(False)
    self.all_widgets.get_widget('download_pkg_popup_menu').set_sensitive(False)
    self.all_widgets.get_widget('remove_popup_menu').set_sensitive(False)
  # }}}

  # def populate_remote_pkg_info(self): {{{
  def populate_remote_pkg_info(self):
    for repo,v in self.pkgs_by_repo.iteritems():
      for pkg_desc in v:
        name = pkg_desc[0]
        #self.remote_pkg_info[name] = self.shell.info(name)
        self.run_in_thread(self.shell.info, {'what': name})
        self.try_sem_animate_progress_bar()
        if self.shell.get_prev_return() == None:
          print 'None!'
          return None
        
        self.remote_pkg_info[name] = self.shell.get_prev_return()
  # }}}

  # def populate_local_pkg_list(self): {{{
  def populate_local_pkg_list(self):
    #self.local_pkgs = self.shell.local_search()
    
    self.run_in_thread(self.shell.local_search, {})

    # libpypac support {{{
    #self.run_in_thread(self.shell.local_search_pypac, {})
    # }}}
    
    #self.try_sem_animate_progress_bar()
    self.try_sem()

    if self.shell.get_prev_return() == None:
      print 'None!'
      return None
    
    self.local_pkgs = self.shell.get_prev_return()
  # }}}

  # def populate_pkgs_by_repo(self): {{{
  def populate_pkgs_by_repo(self):
    #(self.pkgs_by_repo, self.pkgs) = self.shell.repofiles()
    #(self.pkgs_by_repo, self.pkgs) = self.shell.repofiles2()
    self.run_in_thread(self.shell.repofiles2, {})

    #self.try_sem_animate_progress_bar()
    self.try_sem()

    exit_status = self.shell.get_exit_status()

    if exit_status:
      out = self.shell.__capture_stderr__()
      if out.index('could not open sync database'):
        print 'It seems there is a database that needs sync\'ing: \n' + out 
        print 'Guzuta will take care of this for you and resume normal startup.'
        self.run_in_thread(self.shell.updatedb, {})
        self.try_sem()

        self.run_in_thread(self.shell.repofiles2, {})
        self.try_sem()
    else:
      if self.shell.get_prev_return() == None:
        print 'None!'
        return None
    
    (self.pkgs_by_repo, self.pkgs) = self.shell.get_prev_return()
  # }}}

  # def populate_pkg_lists(self): {{{
  def populate_pkg_lists(self):
    self.populate_local_pkg_list()
    self.populate_pkgs_by_repo()
  # }}}

  # def set_shell(self, shell): {{{
  def set_shell(self, shell):
    self.shell = shell
  # }}}

  # def toggled(self, toggle_renderer, path): {{{
  def toggled(self, toggle_renderer, path):
    # get iter from model
    iter = self.liststore.get_iter_from_string(path)
    # get value
    checked = self.liststore.get_value(iter, 0)
    # toggle it
    checked = not checked
    # set value
    self.liststore.set_value(iter, 0, checked)
  # }}}

  # def __add_pkg_info_markuped_to_pkg_info_label__(self, lines, {{{
  # installed = True):
  def __add_pkg_info_markuped_to_pkg_info_label__(self, lines,
      installed = True):
    pkg_info_label = self.all_widgets.get_widget('pkg_info_label')
    #iterator = text_buffer.get_iter_at_offset(0)
    #table = text_buffer.get_tag_table()
    #tag = table.lookup('bold')
    #if tag == None:
    #  tag = text_buffer.create_tag('bold', weight=pango.WEIGHT_BOLD)
    
    label_text = ''
    if not installed:
      #text_buffer.insert_with_tags_by_name(iterator,
      #    'Package not installed!\n\n', 'bold')
      label_text = label_text + '<b>Package not installed!</b>\n\n'
      
    pattern = ':'

    # add text accordingly, 'bolding' the 'Name    :', etc
    for line in lines:
      line = line.strip()
      if line != '':

        try:
          if line.index('<'):
            line = line.replace('<', ' ')
          if line.index('>'):
            line = line.replace('>', ' ')
          if line.index('@'):
            line = line.replace('@', '.at.')
        except ValueError:
          pass

        match_object = re.search(pattern, line)
        
        if match_object != None:
          bold_stuff = line[:match_object.start()+1].strip()
          normal_stuff = line[match_object.start()+1:].strip()
          if bold_stuff.startswith('Size'):
            raw_size = int(normal_stuff)
            kb_size = raw_size / 1024
            normal_stuff = str(kb_size) + ' KB'
            if kb_size > 1024:
              mb_size = kb_size / 1024
              normal_stuff = str(mb_size) + ' MB'
              if mb_size > 1024:
                gb_size = mb_size / 1024
                normal_stuff = str(gb_size) + ' GB'
          elif bold_stuff.startswith('URL'):
            # underline the url
            normal_stuff = '<u>' + normal_stuff + '</u>'
                
          label_text = label_text + '<b>' + bold_stuff + '</b> ' +\
              normal_stuff + '\n'
        else:
          #text_buffer.insert(iterator, line + '\n')
          label_text = label_text + line.strip() + '\n'
    pkg_info_label.set_markup(label_text)
    #pkg_info_label.set_text(label_text)
  # }}}

  # def __add_pkg_info_markuped_to_text_buffer__(self, text_buffer, {{{
  # lines, installed = True):
  def __add_pkg_info_markuped_to_text_buffer__(self, text_buffer, lines,
      installed = True):
    iterator = text_buffer.get_iter_at_offset(0)
    table = text_buffer.get_tag_table()
    bold_tag = table.lookup('bold')
    hyperlink_tag = table.lookup('hyperlink')

    if bold_tag == None:
      bold_tag = text_buffer.create_tag('bold', weight=700)
    
    if not installed:
      text_buffer.insert_with_tags_by_name(iterator,
          'Package not installed!\n\n', 'bold')
      
    pattern = ':'

    # add text accordingly, 'bolding' the 'Name    :', etc
    for line in lines:
      if line != '':

        match_object = re.search(pattern, line)
        
        if match_object != None:
          bold_stuff = line[:match_object.start()+1]
          normal_stuff = line[match_object.start()+1:]

          text_buffer.insert_with_tags_by_name(iterator,
              bold_stuff, 'bold')
        
          if bold_stuff.startswith('Size'):
            raw_size = int(normal_stuff)
            kb_size = raw_size / 1024
            normal_stuff = str(kb_size) + ' KB'
            if kb_size > 1024:
              mb_size = kb_size / 1024
              normal_stuff = str(mb_size) + ' MB'
              if mb_size > 1024:
                gb_size = mb_size / 1024
                normal_stuff = str(gb_size) + ' GB'
            text_buffer.insert(iterator, normal_stuff +\
                '\n')
          elif line.startswith('URL'):
            if hyperlink_tag == None:
              extra = normal_stuff
              hyperlink_tag = text_buffer.create_tag('hyperlink',
                  foreground='blue', underline = self.pango_underline_single)

              def anonymous_hyperlink(tag,widget,event,iterator):
                if event.type == gtk.gdk.BUTTON_PRESS:
                  return self.on_hyperlink_clicked(tag,widget,event,iterator,\
                      extra)

              #textbuffer.connect('motion_notify_event', self.on_hyperlink_motion)
              hyperlink_tag.connect('event', anonymous_hyperlink)

            #text_buffer.insert_with_tags(iterator, normal_stuff + '\n',\
            #    hyperlink_tag)
            text_buffer.insert_with_tags_by_name(iterator, normal_stuff +\
                '\n', 'hyperlink')
            self.url_tags.append(hyperlink_tag)
          else:
            text_buffer.insert(iterator, normal_stuff + '\n')
        else:
          text_buffer.insert(iterator, line + '\n')
  # }}}

  # def __refresh_pkgs_treeview__(self): {{{
  def __refresh_pkgs_treeview__(self):
    new_liststore = gtk.ListStore('gboolean', str, str, str)
    
    new_liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
    for row in self.liststore:
      name = row[1]
      try:
        installed_version = self.local_pkgs[name][1]
      except KeyError:
        installed_version = '--'
      try:
        available_version = self.pkgs[name][1]
      except KeyError:
        available_version = '--'
      
      new_liststore.append([False, name, installed_version, available_version])
    self.liststore = new_liststore
    self.treeview.set_model(self.liststore)
  # }}}

  # def __fill_treeview_with_pkgs_from_repo__(self, repo): {{{
  def __fill_treeview_with_pkgs_from_repo__(self, repo):
    self.treeview.set_model(None) # unsetting model to speed things up

    self.liststore = gtk.ListStore('gboolean', str, str, str)

    if repo == 'current' or repo == 'extra' or repo == 'community':
      # current, extra, community {{{
      for v in self.pkgs_by_repo[repo]:
        
        name = v[0] # name
        try:
          # repo, version, description
          installed_version = self.local_pkgs[name][1]
        except KeyError:
          # not installed
          #try:
          #  self.not_installed[name]
          #except KeyError:
          #  self.not_installed[name] = None
          installed_version = '--'
        
        self.liststore.append([False, v[0], installed_version, v[1]])
      # }}}
    elif repo == 'installed':
      # installed {{{
      for name, v in self.local_pkgs.iteritems():
        #available version
        try:
          available_version = self.pkgs[name][1]
        except KeyError:
          # pkg was installed separately
          available_version = '--'
          
        self.liststore.append([False, name, v[1], available_version])
      # }}}
    elif repo == 'all':
      # all {{{
      # community, extra, current
      for repo,v in self.pkgs_by_repo.iteritems():
        for pkg in v:

          name = pkg[0] # name
          try:
            installed_version = self.local_pkgs[name][1]
          except KeyError:
            #try:
            #  self.not_installed[name]
            #except KeyError:
            #  self.not_installed[name] = None
            installed_version = '--'

          self.liststore.append([False, pkg[0], installed_version, pkg[1]])
      # }}}
    elif repo == 'not installed':
      # not installed {{{
      not_installed = xor_two_dicts(self.local_pkgs, self.pkgs)
      # pkg: repo, version
      for name, v in not_installed.iteritems():
        self.liststore.append([False, name, '--', v[1]])
      # }}}
    elif repo == 'last installed':
      # TODO: last installed {{{
      pass
      # }}}
    elif repo == 'last uninstalled':
      # TODO: last uninstalled {{{
      pass
      # }}}
    elif repo == 'no repository':
      # no repository {{{
      try:
        self.pkgs_by_repo[repo]
      except KeyError:
        return

      for v in self.pkgs_by_repo[repo]:
        pass
        
        #name = v[0] # name
        #try:
        #  # repo, version, description
        #  installed_version = self.local_pkgs[name][1]
        #except KeyError:
        #  # not installed
        #  #try:
        #  #  self.not_installed[name]
        #  #except KeyError:
        #  #  self.not_installed[name] = None
        #  installed_version = '--'
        #
        #self.liststore.append([False, v[0], installed_version, v[1]])
      # }}}
    else:
      # something else {{{
      for v in self.pkgs_by_repo[repo]:
        
        name = v[0] # name
        try:
          # repo, version, description
          installed_version = self.local_pkgs[name][1]
        except KeyError:
          # not installed
          #try:
          #  self.not_installed[name]
          #except KeyError:
          #  self.not_installed[name] = None
          installed_version = '--'
        
        self.liststore.append([False, v[0], installed_version, v[1]])
      # }}}
    self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)
    self.treeview.set_model(self.liststore)
  # }}}

  # def __is_root__(self): {{{
  def __is_root__(self):
    uid = posix.getuid()
    return uid == 0
  # }}}

  # def get_all_selected_packages(tree_model): {{{
  # TODO: put outside of class
  def get_all_selected_packages(self, tree_model):
    n = len(tree_model)
    
    names = []
    for i in range(n):
      if tree_model[i][0]:
        names.append(tree_model[i][1])

    return names
  # }}}

  # def refresh_pkgs_treeview(self): {{{
  def refresh_pkgs_treeview(self):
    selection = self.treeview_repos.get_selection()
    treemodel, iter = selection.get_selected()

    if not iter:
      self.__refresh_pkgs_treeview__()
    else:
      repo = treemodel.get_value(iter, 0)
      # fill treeview with pkgs from 'repo'
      self.__fill_treeview_with_pkgs_from_repo__(repo.lower())
  # }}}

  # def __add_pkg_info_to_local_pkgs__(self, pkg_list): {{{
  def __add_pkg_info_to_local_pkgs__(self, pkg_list):
    for installed_pkg in pkg_list:
      # get repo, version, description in local search 
      # and put it in self.local_pkgs and put info in
      # self.local_pkg_info
      info = ''
      try:
        info = self.local_pkg_info[installed_pkg]
      except KeyError:
        try:
          info = self.remote_pkg_info[installed_pkg]
        except KeyError:
          #info = self.shell.info(installed_pkg)
          self.run_in_thread(self.shell.info, {'what': installed_pkg})
          self.try_sem()
          if self.shell.get_prev_return() == None:
            print 'None!'
            return None
          
          info = self.shell.get_prev_return()
        self.local_pkg_info[installed_pkg] = info

      if info == None:
        try:
          info = self.remote_pkg_info[installed_pkg]
          self.local_pkg_info[installed_pkg] = info
        except KeyError:
          #info = self.shell.local_info(installed_pkg)
          self.run_in_thread(self.shell.local_info, {'what': installed_pkg})
          self.try_sem()
          if self.shell.get_prev_return() == None:
            print 'None!'
            return None
          
          info = self.shell.get_prev_return()
          self.local_pkg_info[installed_pkg] = info

      n = len(info)
      repo = ''
      version = ''
      description = ''

      for i in range(n):
        line = info[i]
        if line.startswith('Repository'):
          # format: Repository whitespace: repo
          pos = line.index(':')
          repo = line[pos+1:].strip()
        elif line.startswith('Version'):
          version = line[line.index(':')+1:].strip()
        elif line.startswith('Description'):
          description = line[line.index(':')+1:].strip()
          
          try:
            info[i+1].index(':')
          except ValueError:
            # no ':' found
            description = description + ' ' + info[i+1].strip()
            # skip next iteration
            i = i+1
        else:
          pass
      self.local_pkgs[installed_pkg] = (repo, version, description)
  # }}}

  # def remove_packages(self, pkg_list): {{{
  def remove_packages(self, pkg_list):
    what = ''

    for pkg_name in pkg_list:
      what = what + pkg_name + ' '
    
    #self.remove_noconfirm(what)
    #(exit_status, dependencies, out) = self.shell.remove(what)
    self.run_in_thread(self.shell.remove, {'what': what})
    self.try_sem_animate_progress_bar()
    if self.shell.get_prev_return() == None:
      print 'None!'
      return None
    
    (exit_status, dependencies, out) = self.shell.get_prev_return()
    return (exit_status, dependencies, out)
  # }}}
# }}}

