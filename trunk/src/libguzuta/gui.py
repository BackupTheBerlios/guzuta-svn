#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim:set fdm=marker:

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
import math, sys

# "our" trayicon
import trayicon
import signal

from shell import *
# }}}

# def xor_two_dicts(a, b): {{{
# return all things that are in 'b' and that are not in 'a'
def xor_two_dicts(a, b):
  ret = {}
  for key, value in b.iteritems():
    if key not in a:
      ret[key] = value

  return ret
# }}}
    
# def toggled(cellrenderer, path, model): {{{
def toggled(cellrenderer, path, model):
  model[path][0] = not model[path][0]
# }}}

# class gui: {{{
class gui:
  pango_no_underline = 0
  pango_underline_single = 1

  # from: http://async.com.br/faq/pygtk/index.py?req=show&file=faq10.017.htp
  # def dialog_response_cb(self, dialog, response_id): {{{
  def dialog_response_cb(self, dialog, response_id):
    dialog.hide()

    self.response2 = response_id
    self.dialog_ended_event.set()
    return False
  # }}}

  # def dialog_run(self, dialog): {{{
  def dialog_run(self, dialog):
    self.response2 = None
    if not dialog.modal:
      dialog.set_modal(True)

    self.dialog_ended_event = threading.Event()
    self.dialog_ended_event.clear()

    dialog.connect('response', self.dialog_response_cb)
    dialog.show()

    while not self.dialog_ended_event.isSet():
      self.dialog_ended_event.wait(0.01)
      while gtk.events_pending():
        gtk.main_iteration(False)
    self.dialog_ended_event.clear()
  # }}}

  # def alpm_progress_bar_set_text_and_fraction(self, progress_bar, {{{
  #     text, append_text, frac):
  def alpm_progress_bar_set_text_and_fraction(self, progress_bar, text,
      append_text, frac):
    gtk.gdk.threads_enter()
    if append_text:
      t = progress_bar.get_text() + text
    else:
      t = text
    progress_bar.set_text(t)
    #print 'setting fraction ', frac
    progress_bar.set_fraction(frac)
    gtk.gdk.threads_leave()
    return False
  # }}}

  # def gui_trans_cb_ev(self, event, package1, package2): {{{
  def gui_trans_cb_ev(self, event, package1, package2):
    prev_text = ''
    time.sleep(1)
    
    text = ''
    append_text = False
    print 'event: ', event, self.busy_dialog, self.busy_progress_bar3
    if event == alpm.PM_TRANS_EVT_CHECKDEPS_START:
      print 'PM_TRANS_EVT_CHECKDEPS_START'
      print 'Checking dependencies... '
      text = 'checking dependencies... '
    
    elif event == alpm.PM_TRANS_EVT_FILECONFLICTS_START:
      print 'PM_TRANS_EVT_FILECONFLICTS_START'
      print 'checking for file conflicts... '
      text = 'checking for file conflicts... '
    
    elif event == alpm.PM_TRANS_EVT_RESOLVEDEPS_START:
      print 'PM_TRANS_EVT_RESOLVEDEPS_START'
      print 'resolving dependencies'
      text = 'resolving dependencies... '
    
    elif event == alpm.PM_TRANS_EVT_INTERCONFLICTS_START:
      print 'PM_TRANS_EVT_INTERCONFLICTS_START'
      print 'looking for inter-conflicts... '
      text = 'looking for inter-conflicts... '
    
    elif event == alpm.PM_TRANS_EVT_FILECONFLICTS_START:
      print 'PM_TRANS_EVT_FILECONFLICTS_START'
      print 'checking for file conflicts... '
      text = 'checking for file conflicts... '
    
    elif event == alpm.PM_TRANS_EVT_CHECKDEPS_DONE:
      print 'PM_TRANS_EVT_CHECKDEPS_DONE'
      print 'done.'
      text = 'done'
      append_text = True
    
    elif event == alpm.PM_TRANS_EVT_FILECONFLICTS_DONE:
      print 'PM_TRANS_EVT_FILECONFLICTS_DONE'
      print 'done.'
      text = 'done'
      append_text = True
    
    elif event == alpm.PM_TRANS_EVT_RESOLVEDEPS_DONE:
      print 'PM_TRANS_EVT_RESOLVEDEPS_DONE'
      print 'done.'
      text = 'done'
      append_text = True
    
    elif event == alpm.PM_TRANS_EVT_INTERCONFLICTS_DONE:
      print 'PM_TRANS_EVT_INTERCONFLICTS_DONE'
      print 'done.'
      text = 'done'
      append_text = True
    
    elif event == alpm.PM_TRANS_EVT_ADD_START:
      print 'PM_TRANS_EVT_ADD_START'
      print 'installing %s... ' % package1.get_name()
      text = 'installing %s... ' % package1.get_name()
    
    elif event == alpm.PM_TRANS_EVT_ADD_DONE:
      print 'PM_TRANS_EVT_ADD_DONE'
      print 'done.'
      text = 'done'
      append_text = True

    elif event == alpm.PM_TRANS_EVT_REMOVE_START:
      print 'PM_TRANS_EVT_REMOVE_START'
      print 'removing %s... ' % package1.get_name()
      text = 'removing %s... ' % package1.get_name()
    
    elif event == alpm.PM_TRANS_EVT_REMOVE_DONE:
      print 'PM_TRANS_EVT_REMODE_DONE'
      print 'done.'
      text = 'done'
      append_text = True
    
    elif event == alpm.PM_TRANS_EVT_UPGRADE_START:
      print 'PM_TRANS_EVT_UPGRADE_START'
      print 'upgrading %s... ' % package1.get_name()
      text = 'upgrading %s... ' % package1.get_name()
    
    elif event == alpm.PM_TRANS_EVT_UPGRADE_DONE:
      print 'PM_TRANS_EVT_UPGRADE_DONE'
      print 'done.'
      text = 'done'
      append_text = True

    self.current_fraction = self.current_fraction + self.fraction_increment
    gobject.idle_add(self.alpm_progress_bar_set_text_and_fraction,\
        self.busy_progress_bar3, text, append_text, self.current_fraction)

  # }}}

  # def gui_trans_cb_conv(self, event, data1, data2, data3): {{{
  def gui_trans_cb_conv(self, event, data1, data2, data3):
    self.response = None
    response = 0
    id = gobject.idle_add(self.gui_trans_cb_conv2, event, data1, data2, data3)
    while not self.dialog_ended_event.isSet():
      while gtk.events_pending():
        gtk.main_iteration(False)
      time.sleep(0.1)
    gobject.source_remove(id)
    self.dialog_ended_event.clear()
    return self.response
  # }}}

  # def gui_trans_cb_conv2(self, event, data1, data2, data3): {{{
  def gui_trans_cb_conv2(self, event, data1, data2, data3):
    # return > 0 means to go ahead and replace/install ignoring, etc
    # return == 0 means to stop
    print 'Question:', (event, data1, data2, data3)

    #time.sleep(1)
    gtk.gdk.threads_enter()
    cb_conv_question_dialog =\
        self.all_widgets.get_widget('cb_conv_question_dialog')
    cb_conv_reason_label =\
        self.all_widgets.get_widget('cb_conv_reason_label')
    cb_conv_action_label =\
        self.all_widgets.get_widget('cb_conv_action_label')
    if event == alpm.PM_TRANS_CONV_INSTALL_IGNOREPKG:
      cb_conv_reason_label.set_markup(\
          '<b>%s</b> requires <b>%s</b>, but it is in IgnorePkg.' %\
          (data1.get_name(), data2.get_name()))
      cb_conv_action_label.set_markup('<i>Install anyway?</i>')

    elif event == alpm.PM_TRANS_CONV_REPLACE_PKG:
      cb_conv_action_label.set_markup(\
          'Replace <b>%s</b> with <b>%s/%s</b>?' %\
          (data1.get_name(), data3, data2.get_name()))

    elif event == alpm.PM_TRANS_CONV_CONFLICT_PKG:
      cb_conv_reason_label.set_markup(\
          '<b>%s</b> conflicts with <b>%s</b>' %\
          (data1, data2))
      cb_conv_action_label.set_markup(\
          '<i>Do you want to remove <b>%s</b>?</i>' %\
          data2)

    elif event == alpm.PM_TRANS_CONV_LOCAL_NEWER:
      cb_conv_reason_label.set_markup(\
          'Local version of <b>%s-%s</b> is newer.' %\
          (data1.get_name(), data1.get_version()))
      cb_conv_action_label.set_markup('<i>Upgrade anyway?</i>')

    elif event == alpm.PM_TRANS_CONV_LOCAL_UPTODATE:
      cb_conv_reason_label.set_markup(\
          'Local version of <b>%s-%s</b> is up to date.' %\
          (data1.get_name(), data1.get_version()))
      cb_conv_action_label.set_markup('<i>Upgrade anyway?</i>')

    self.response = None
    self.dialog_ended_event.clear()
    self.dialog_run(cb_conv_question_dialog)
    resp = self.response2

    if resp == gtk.RESPONSE_OK:
      self.response = 1
    else:
      self.response = 0
    gtk.gdk.threads_leave()
    self.dialog_ended_event.set()
    return False
  # }}}

  # def __init__(self): {{{
  def __init__(self):
    gtk.gdk.threads_init()
    self.report_hook_started = False
    self.report_hook_start = None
    self.report_hook_now = None
    
    self.cancel_operation = False
    self.th = None
    self.prev_return = None

    self.column_selected = False

    self.dialog_ended_event = threading.Event()
    self.dialog_ended_event.clear()
    self.lock = threading.Lock()
    self.thread_started_lock = threading.Lock()
    self.thread_started_lock.acquire()

    self.cwd = os.environ['PWD']

    self.cancelled = False

    self.toggle_handler_id = None
    self.toggle_handler_id2 = None

    fname = self.cwd + '/share/guzuta/guzuta3.glade'
    if os.path.exists(fname):
      self.glade_file = fname
    elif os.path.exists('/usr/share/guzuta/guzuta3.glade'):
      fname = '/usr/share/guzuta/guzuta3.glade'
      self.glade_file = fname
    elif os.path.exists('guzuta3.glade'):
      fname = 'guzuta3.glade'
      self.glade_file = fname
    else:
        print __name__
        print os.getcwd()
        print 'no glade file found!'
        sys.exit(2)

    # signals dictionary {{{
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
    'on_install_pkg_clicked': self.on_install_pkg_clicked,
    'on_remove_pkg_clicked': self.on_remove_pkg_clicked,
    'on_install_pkg_popup_delete_event': self.on_install_pkg_popup_delete_event,
    'on_install_pkg_popup_destroy': self.on_install_pkg_popup_destroy,
    'on_search_clicked': self.on_search_clicked,
    'on_clear_clicked': self.on_clear_clicked,
    #'on_search_entry_activate': self.on_search_clicked,
    'on_search_entry_changed': self.on_search_changed,
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
    'on_cache_menu_activate':\
        self.on_cache_menu_activate,
    'on_view_files_popup_menu_activate':\
        self.on_view_files_popup_menu_activate,
    #'on_cancel_busy_button_clicked':\
    #    self.on_cancel_busy_button_clicked,
    'on_information_text_motion_notify_event':\
        self.motion_notify_event,
    'on_information_text_visibility_notify_event':\
        self.visibility_notify_event,
    'on_information_text_event_after':\
        self.event_after,
    'on_busy_cancel_button_clicked':\
        self.on_busy_cancel_button_clicked
    #'on_browse_preferences_button_clicked':\
    #    self.on_browse_preferences_button_clicked,
    #'on_information_text_leave_notify_event':\
    #  self.on_mainwindow_motion_notify_event,
    #'on_mainwindow_enter_notify_event': self.on_mainwindow_enter_notify_event
    #'on_mainwindow_motion_notify_event': self.on_mainwindow_motion_notify_event,
    #'on_systray_eventbox_button_press_event':\
    #    self.on_systray_eventbox_button_press_event,
    #'on_systray_eventbox_motion_notify_event':\
    #    self.on_systray_eventbox_motion_notify_event,
    #'on_systray_eventbox_leave_notify_event':\
    #    self.on_systray_eventbox_leave_notify_event
    }
    # end signals
    # }}}

    self.treeview = None
    self.uid = posix.getuid()
    self.pkgs = {}
    self.local_pkg_info = {}
    self.remote_pkg_info = {}

    self.pkgs_in_local = {}

    self.pkgs_by_repo = {}
    self.pkgs_by_repo['no repository'] = []

    self.downloading_db = True
    self.url_tags = []
    self.underlined_url = False

    self.not_installed = {}
    self.trayicon = None
    self.systray_eventbox = None

    self.hovering_over_link = False
    self.hand_cursor = gtk.gdk.Cursor(gtk.gdk.HAND2)
    self.regular_cursor = gtk.gdk.Cursor(gtk.gdk.XTERM)

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

    guzuta_debug = alpm.PM_LOG_WARNING | alpm.PM_LOG_FLOW1 | alpm.PM_LOG_FLOW2\
        | alpm.PM_LOG_DEBUG | alpm.PM_LOG_ERROR | alpm.PM_LOG_FUNCTION
    #guzuta_debug = 0xFF
    #guzuta_debug = alpm.PM_LOG_WARNING | alpm.PM_LOG_ERROR
    self.shell = shell(command_line = None, lock = self.lock,\
        debug = guzuta_debug,
        interactive = True)
    self.populate_pkg_lists()
    self.populate_pkg_lists2()
    self.dbs_by_name = self.shell.alpm_get_dbs_by_name()
    # pid of pacman process
    self.pid = 0

    self.main_window = self.all_widgets.get_widget("mainwindow")
    # checkbox, name, version, packager, description
    self.treeview = self.all_widgets.get_widget('treeview')
    # sortable
    self.treeview_repos = self.all_widgets.get_widget('treeview_repos')
    self.vbox2 = self.all_widgets.get_widget('vbox2')
    self.quit_item = self.all_widgets.get_widget('quit')
    self.update_db = self.all_widgets.get_widget('update_db')
    self.search_entry = self.all_widgets.get_widget('search_entry')
    
    self.information_text = self.all_widgets.get_widget('information_text')

    self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar3')

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

    try:
      self.guzuta_icon =\
        gtk.gdk.pixbuf_new_from_file(self.cwd + \
          '/share/guzuta/guzuta_icon_transparent.png')
    except gobject.GError:
      self.guzuta_icon =\
          gtk.gdk.pixbuf_new_from_file(\
            '/usr/share/guzuta/guzuta_icon_transparent.png'\
          )
    self.main_window.set_icon(self.guzuta_icon)
    self.main_window.show()

    self.__build_trayicon__()
    # trayicon
    self.trayicon.show_all()
    
    if not self.__is_root__():
      self.__disable_all_root_widgets__()
      not_root_dialog = self.all_widgets.get_widget('not_root_dialog')
      self.current_dialog = not_root_dialog

      self.main_window.set_sensitive(False)
      self.current_dialog_on = True
      not_root_dialog.run()
      not_root_dialog.hide()
      self.current_dialog_on = False
      self.main_window.set_sensitive(True)
      #sys.exit(1)

    gtk.main()
  # }}}
  
  # def toggled(self, toggle_renderer, path, store = None, col = 0): {{{
  def toggled(self, toggle_renderer, path, store = None, col = 0):
    treemodelrow = store[path]
    for row in treemodelrow.iterchildren():
      store[row.path][col] = not store[path][col]
    store[path][col] = not store[path][col]
  # }}}

  # def on_treeview_column_clicked(self, treeviewcolumn, liststore, {{{
  #     col):
  def on_treeview_column_clicked(self, treeviewcolumn, store, col):
    self.column_selected = not self.column_selected
    
    for row in store:
      for child_row in row.iterchildren():
        store[child_row.path][col] = self.column_selected
      store[row.path][col] = self.column_selected
    
    #print '-------------------------'
    #for row in store:
    #  for child_row in row.iterchildren():
    #    if store[child_row.path][col] == True:
    #      print store[child_row.path][0]
    #  if store[row.path][col] == True:
    #    print store[row.path][0]
    #print '--------------END---------'
    return True
  # }}}

  # def cancel_cb(self): {{{
  def cancel_cb(self):
    return self.cancel_operation
  # }}}

  # def run_in_thread(self, method, args_dict, wait=False): {{{
  def run_in_thread(self, method, args_dict, wait=False):
    self.th = threading.Thread(target=method, kwargs=args_dict)
    self.th.start()
    if wait:
      self.th.join()
  # }}}

  # def alpm_debug_cb(self): {{{
  def alpm_debug_cb(self):
    #print 'STILL ALIVE'
    return True
  # }}}

  # def alpm_run_in_thread_and_wait(self, method, args): {{{
  def alpm_run_in_thread_and_wait(self, method, args):
    th_obj = None
    self.run_in_thread(method, args)

    cb_id = gobject.timeout_add(10, self.alpm_debug_cb)
    # waiting for thread to finish
    while not self.shell.th_ended_event.isSet():
      self.shell.th_ended_event.wait(0.001)

      while gtk.events_pending():
        gtk.main_iteration(False)

    self.shell.th_ended_event.clear()
    gobject.source_remove(cb_id)
  # }}}

  # def alpm_urllib_report_hook(self, blocks_so_far, block_size_bytes, {{{
  #   total_size):
  def alpm_urllib_report_hook(self, blocks_so_far, block_size_bytes,
      total_size):
    # magical sleep, without this, guzuta crashes cairo
    time.sleep(0.002)

    if not self.report_hook_started:
      self.report_hook_started = True
      self.report_hook_start = time.time()
      #print 'self.report_hook_start is: ', self.report_hook_start
    else:
      self.report_hook_now = time.time()
      #print 'self.report_hook_now is: ', self.report_hook_now

    if total_size < block_size_bytes:
      total_blocks = 1
    else:
      total_blocks = math.ceil(float(total_size)/float(block_size_bytes))

    bytes_so_far = blocks_so_far * block_size_bytes
    if self.report_hook_now == None:
      seconds_so_far = 0
      kbps = 0
    else:
      seconds_so_far = self.report_hook_now - self.report_hook_start
      # kb/s = kbs downloaded so far / seconds elapsed
      kbps = (bytes_so_far / 1024) / seconds_so_far
    division = float(blocks_so_far) / float(total_blocks)
    #self.busy_progress_bar3.set_text('Downloading ' + self.shell.retrieving + ' ' + str(division * 100) + '%')
    #self.busy_progress_bar3.set_text('%.1f %% - %.1f kb/s' % (division * 100, kbps))
    #self.busy_progress_bar3.set_text('%d out of %d bytes' %\
    #    ((blocks_so_far * block_size_bytes), total_size))
    if self.downloading_db:
      self.busy_progress_bar3.set_text('%.1f %% - %.1f kb/s' % (division * 100, kbps))
      self.busy_status_label.set_markup('<i>Downloading database \'%s\'...</i>' %
          (self.shell.retrieving))
    else:
      string = ('<i>Downloading \'%s\'...</i>' % self.shell.retrieving)
      #print 'SETTING STATUS LABEL TO: ', string
      #print 'busy_status_label: ', self.busy_status_label
      self.busy_status_label.set_markup(string)
      #print 'RESULT: <', self.busy_status_label.get_text(), '>'
      self.busy_progress_bar3.set_text('%.1f %% - %.1f kb/s' % (division * 100, kbps))
    if self.busy_progress_bar3:
      self.busy_progress_bar3.set_fraction(division)
  # }}}

  # def alpm_get_group(self, name, repo): {{{
  def alpm_get_group(self, name, repo):
    db = self.dbs_by_name[repo]
    try:
      pkg = db.read_pkg(name)
    except alpm.NoSuchPackageException:
      try:
        group = db.read_group(name)
      except alpm.NoSuchGroupException:
        return None
      else:
        return group
    return None
  # }}}

  # def alpm_get_highest_version_of_pkg(self, dict): {{{
  def alpm_get_highest_version_of_pkg(self, dict):
    length = len(dict)
    if length == 1:
      repo = dict.keys()[0]
      return (repo, dict[repo][1], dict[repo][2])
    else:
      v = None
      for _, (repo, version, desc) in dict.iteritems():
        if repo != 'local':
          if v == None:
            v = repo,version,desc
          else:
            if version > v:
              v = repo,version,desc

      return v
  # }}}

  # def alpm_fill_treestore_with_pkgs_and_grps(self, treeview, treestore, {{{
  # pkgs, groups, repo_name = None):
  def alpm_fill_treestore_with_pkgs_and_grps(self, treeview, treestore, pkgs, groups,
      repo_name = None):
    import cgi
    treeview.set_model(None)
    already_visited_pkgs = {}
    already_visited_grps = {}

    keys = sorted(pkgs.keys() + groups.keys())

    for k in keys:
      if k in groups:
        if k not in already_visited_grps:
          grp_name = k
          already_visited_grps[grp_name] = None
          pkg_names = groups[grp_name]

          if repo_name:
            text = '<b>%s</b>\n<small><i>group</i></small>' %\
              cgi.escape(grp_name)
            text_repo_name = '<b>%s</b>' % cgi.escape(repo_name)
            iter = treestore.append(None, [grp_name, False, text, '', '',\
                text_repo_name])
          else:
            try:
              repo2 = self.groups[grp_name][0]
            except KeyError:
              repo2 = 'local'

            text = '<b>%s</b>\n<small><i>group</i></small>' %\
              cgi.escape(grp_name)
            text_repo_name = '<b>%s</b>' % cgi.escape(repo2)
            iter = treestore.append(None, [grp_name, False, text, '', '',\
                text_repo_name])

          for pkg_name in pkg_names:
            already_visited_pkgs[pkg_name] = None

            try:
              local_version = self.local_pkgs[pkg_name][1]
            except KeyError:
              local_version = '--'

            #available version
            if repo_name:
              available_version = self.pkgs[pkg_name][repo_name][1]
              desc = self.pkgs[pkg_name][repo_name][2]
            else:
              pkg_repo, available_version, desc =\
                self.alpm_get_highest_version_of_pkg(self.pkgs[pkg_name])
              pkg_repo = cgi.escape(pkg_repo)
              if pkg_repo == 'local':
                available_version = '--'

            #if len(desc) > 40:
            #  desc = desc[:40]
            #  desc += ' ...'
            desc = cgi.escape(desc)
              
            if repo_name:
              #treestore.append(iter, [False, pkg_name, local_version,
              #    available_version, repo_name])
              pkg_name = cgi.escape(pkg_name)
              desc = cgi.escape(desc)
              text = '<b>%s</b>\n<small><i>%s</i></small>' % (pkg_name, desc)
              text_local_ver = '<b>%s</b>' % cgi.escape(local_version)
              text_avai_ver = '<b>%s</b>' % cgi.escape(available_version)
              text_repo_name = '<b>%s</b>' % cgi.escape(repo_name)
              treestore.append(iter, [pkg_name, False, text,text_local_ver,
                  text_avai_ver, text_repo_name])
              yield True
            else:
              l = len(self.pkgs[pkg_name].keys())

              if l > 1:
                for repo3 in self.pkgs[pkg_name].keys():
                  if repo3 != 'local':
                    #treestore.append(iter, [False, pkg_name, local_version,
                    #    available_version, repo3])
                    pkg_name = cgi.escape(pkg_name)
                    desc = cgi.escape(desc)
                    text = '<b>%s</b>\n<small><i>%s</i></small>' % (pkg_name, desc)
                    text_local_ver = '<b>%s</b>' % cgi.escape(local_version)
                    text_avai_ver = '<b>%s</b>' % cgi.escape(available_version)
                    text_repo_name = '<b>%s</b>' % cgi.escape(repo3)
                    treestore.append(iter, [pkg_name, False, text,
                        text_local_ver,
                        text_avai_ver, text_repo_name])
                    local_info = (iter, [False, pkg_name, local_version,
                        available_version, repo3])
              else:
                #treestore.append(iter, [False, pkg_name, local_version,
                #    available_version, repo2])
                pkg_name = cgi.escape(pkg_name)
                desc = cgi.escape(desc)
                text = '<b>%s</b>\n<small><i>%s</i></small>' % (pkg_name, desc)
                text_local_ver = '<b>%s</b>' % cgi.escape(local_version)
                text_avai_ver = '<b>%s</b>' % cgi.escape(available_version)
                text_repo_name = '<b>%s</b>' % cgi.escape(repo2)
                treestore.append(iter, [pkg_name, False, text,
                    text_local_ver, text_avai_ver, text_repo_name])
              yield True
      else: # package
        if k not in already_visited_pkgs:
          try:
            local_version = self.local_pkgs[k][1]
          except KeyError:
            local_version = '--'
          
          #available version
          if repo_name:
            available_version =\
                self.pkgs[k][repo_name][1]
            desc = self.pkgs[k][repo_name][2]
          else:
            #pkg_repo, available_version, desc =\
            #    self.alpm_get_highest_version_of_pkg(self.pkgs[k])
            coisa = self.alpm_get_highest_version_of_pkg(self.pkgs[k])
            pkg_repo, available_version, desc = coisa
            desc = cgi.escape(desc)
            if pkg_repo == 'local':
              available_version = '--'

          #if len(desc) > 40:
          #  desc = desc[:40]
          #  desc += ' ...'
          pkg_name = cgi.escape(k)
          if repo_name:
            #treestore.append(None, [False, pkg_name, local_version,\
            #    available_version, repo_name])
            pkg_name = cgi.escape(pkg_name)
            desc = cgi.escape(desc)
            text = '<b>%s</b>\n<small><i>%s</i></small>' % (pkg_name, desc)
            text_local_ver = '<b>%s</b>' % cgi.escape(local_version)
            text_avai_ver = '<b>%s</b>' % cgi.escape(available_version)
            text_repo_name = '<b>%s</b>' % cgi.escape(repo_name)
            treestore.append(None, [pkg_name, False, text,
              text_local_ver, text_avai_ver, text_repo_name])
            yield True
          else:
            for repo3 in self.pkgs[pkg_name].keys():
              if repo3 != 'local':
                #treestore.append(None, [False, pkg_name, local_version,\
                #    available_version, repo3])
                pkg_name = cgi.escape(pkg_name)
                desc = cgi.escape(desc)
                text = '<b>%s</b>\n<small><i>%s</i></small>' % (pkg_name, desc)
                text_local_ver = '<b>%s</b>' % cgi.escape(local_version)
                text_avai_ver = '<b>%s</b>' % cgi.escape(available_version)
                text_repo_name = '<b>%s</b>' % cgi.escape(repo3)
                treestore.append(None, [pkg_name, False, text,
                    text_local_ver, text_avai_ver, text_repo_name])
              yield True
    treeview.set_model(treestore)
    yield False
  # }}}

  # def __setup_pkg_treeview__(self): {{{
  def __setup_pkg_treeview__(self):
    self.__setup_pkg_treeview_no_fill__()
    self.local_groups = self.shell.alpm_get_groups('local')

    gobject.idle_add(self.alpm_fill_treestore_with_pkgs_and_grps(\
        self.treeview, self.liststore, self.local_pkgs, self.local_groups\
        ).next)
    #self.alpm_fill_treestore_with_pkgs_and_grps(self.treeview, self.liststore,\
    #    self.local_pkgs, self.local_groups)
    self.treeview.set_model(self.liststore)
  # }}}
  
  # def __setup_pkg_treeview_no_fill__(self, store = None): {{{
  def __setup_pkg_treeview_no_fill__(self, store = None):
    if not store:
      self.liststore = gtk.TreeStore('gchararray', 'gboolean', 'gchararray', 'gchararray',\
          'gchararray', 'gchararray')

    self.textrenderer = gtk.CellRendererText()
    self.togglerenderer = gtk.CellRendererToggle()
    self.togglerenderer.set_active(True)

    if self.toggle_handler_id:
      if not self.togglerenderer.handler_is_connected(self.toggle_handler_id):
        self.toggle_handler_id = self.togglerenderer.connect('toggled',\
          self.toggled, self.liststore, 1)
      else:
        self.togglerenderer.disconnect(self.toggle_handler_id)
        self.toggle_handler_id = self.togglerenderer.connect('toggled',\
          self.toggled, self.liststore, 1)
    else:
      self.toggle_handler_id = self.togglerenderer.connect('toggled',\
          self.toggled, self.liststore, 1)

    for column in self.treeview.get_columns():
      self.treeview.remove_column(column)

    self.emptycolumn = gtk.TreeViewColumn('')
    self.emptycolumn.pack_start(self.togglerenderer)
    self.emptycolumn.set_attributes(self.togglerenderer, active=1)
    self.emptycolumn.set_clickable(True)
    self.emptycolumn.connect('clicked', self.on_treeview_column_clicked,\
        self.liststore, 1)
    
    self.namecolumn = gtk.TreeViewColumn('Name', self.textrenderer, markup=2)
    self.namecolumn.set_resizable(True)
    self.namecolumn.set_min_width(300)
    self.namecolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
    self.namecolumn.set_sort_column_id(0)
    
    self.installedversioncolumn = gtk.TreeViewColumn('Installed')
    self.installedversioncolumn.set_sort_column_id(3)
    self.installedversioncolumn.pack_start(self.textrenderer)
    #self.installedversioncolumn.set_attributes(self.textrenderer, text=3)
    self.installedversioncolumn.set_attributes(self.textrenderer, markup=3)
    
    self.availableversioncolumn = gtk.TreeViewColumn('Available')
    self.availableversioncolumn.set_sort_column_id(4)
    self.availableversioncolumn.pack_start(self.textrenderer)
    #self.availableversioncolumn.set_attributes(self.textrenderer, text=4)
    self.availableversioncolumn.set_attributes(self.textrenderer, markup=4)

    self.repositorycolumn = gtk.TreeViewColumn('Repository')
    self.repositorycolumn.set_sort_column_id(5)
    self.repositorycolumn.pack_start(self.textrenderer)
    #self.repositorycolumn.set_attributes(self.textrenderer, text=5)
    self.repositorycolumn.set_attributes(self.textrenderer, markup=5)
    
    self.treeview.append_column(self.emptycolumn)
    self.treeview.append_column(self.namecolumn)
    self.treeview.append_column(self.installedversioncolumn)
    self.treeview.append_column(self.availableversioncolumn)
    self.treeview.append_column(self.repositorycolumn)

  # }}}
  
  # def __setup_repo_treeview__(self): {{{
  def __setup_repo_treeview__(self):
    self.treestore_repos = gtk.TreeStore(str, str)

    self.textrenderer_repos = gtk.CellRendererText()

    self.repocolumn = gtk.TreeViewColumn('Repositories',\
        self.textrenderer_repos, markup = 1)
    
    self.treeview_repos.append_column(self.repocolumn)
    

    iter0 = self.treestore_repos.append(None,\
        ['Pseudo Repos', 'Pseudo Repos'])
    self.treestore_repos.append(iter0, ['All', 'All'])
    self.treestore_repos.append(iter0, ['Installed', 'Installed'])
    self.treestore_repos.append(iter0, ['Not Installed',\
        'Not Installed'])
    self.treestore_repos.append(iter0, ['Groups', 'Groups'])
    #self.treestore_repos.append(iter0, ['Explicitly Installed'])
    #self.treestore_repos.append(iter0, ['Last Installed'])
    #self.treestore_repos.append(iter0, ['Last Uninstalled'])

    iter1 = self.treestore_repos.append(None,\
        ['Repos', 'Repos'])
    
    for repo in self.db_names:
      repo = repo.capitalize()
      repo_text = '%s' % repo
      self.treestore_repos.append(iter1, [repo, repo_text])

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

  # signal handlers {{{
  # def on_download_pkg_button_clicked(self, button): {{{
  def on_download_pkg_button_clicked(self, button):
    pkgs_to_download = self.get_all_selected_packages(self.liststore, 1, 0)
    print pkgs_to_download

    if pkgs_to_download == []:
      return 

    root_dir = self.shell.alpm.get_root()
    cache_dir = self.shell.alpm.get_cache_dir()
    ldir = root_dir + cache_dir
    
    files = []
    for pkg_name in pkgs_to_download:
      (_, pkg_ver) = self.shell.alpm_get_pkg_repo(pkg_name)
      
      path = ldir + '/' + pkg_name + '-' + pkg_ver + alpm.PM_EXT_PKG
      files.append(path)

    self.download_packages_from_list(files)
  # }}}
  
  # def on_browse_preferences_button_clicked(self, button): {{{
  def on_browse_preferences_button_clicked(self, button):
    pkg_filechooser_dialog =\
      self.all_widgets.get_widget('pkg_filechooser_dialog')
    self.current_dialog = pkg_filechooser_dialog

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

  # def alpm_depmiss_to_str(self, depmiss): {{{
  def alpm_depmiss_to_str(self, depmiss):
    dep_name = depmiss.get_name()
    dep_ver = depmiss.get_version()
    dep_type = depmiss.get_type()
    dep_target = depmiss.get_target()
    dep_mod = depmiss.get_mod()

    dep_type_str = ''
    if dep_type == alpm.PM_DEP_TYPE_DEPEND:
      dep_type_str = 'requires'
    else:
      dep_type_str = 'is required by'
    str = '%s: %s %s' % (dep_target, dep_type_str, dep_name)

    if dep_mod == alpm.PM_DEP_MOD_EQ:
      str = str + ('=%s' % dep_ver)
    elif dep_mod == alpm.PM_DEP_MOD_GE:
      str = str + ('>=%s' % dep_ver)
    elif dep_mod == alpm.PM_DEP_MOD_LE:
      str = str + ('<=%s' % dep_ver)

    return str
  # }}}

  # def on_install_pkg_from_file_activate(self, menuitem): {{{
  def on_install_pkg_from_file_activate(self, menuitem):
    install_pkg_popup = self.all_widgets.get_widget('install_pkg_popup')

    pkg_filechooser_dialog =\
      self.all_widgets.get_widget('pkg_filechooser_dialog')
    self.current_dialog = pkg_filechooser_dialog
    pkg_filechooser_dialog.set_select_multiple(True)
    
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
      
      pkg_are_you_sure_dialog =\
        self.all_widgets.get_widget('pkg_are_you_sure_dialog2')

      self.are_you_sure_treeview =\
          self.all_widgets.get_widget('pkgs_treeview')

      liststore = gtk.ListStore('gchararray')
      textrenderer = gtk.CellRendererText()

      cols = self.are_you_sure_treeview.get_columns()
      if cols == []:
        namecolumn = gtk.TreeViewColumn('Name')
        namecolumn.set_resizable(True)
        namecolumn.set_min_width(300)
        namecolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        namecolumn.set_sort_column_id(0)
        namecolumn.pack_start(textrenderer)
        namecolumn.set_attributes(textrenderer, text=0)

        self.are_you_sure_treeview.append_column(namecolumn)

      are_you_sure_message_label =\
          self.all_widgets.get_widget('are_you_sure_message_label')

      are_you_sure_message_label.set_text(\
          'Do you wish to remove these packages?')

      for pathname in path_list:
        index = pathname.rfind('/')
        pkg = pathname[index+1:]
        pkg = pkg[:pkg.rfind('-')]
        pkg = pkg[:pkg.rfind('-')]
      #for pkg_name in targets:
        liststore.append([pkg])

      liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)

      self.are_you_sure_treeview.set_model(liststore)

      self.current_dialog_on = True
      response = pkg_are_you_sure_dialog.run()
      pkg_are_you_sure_dialog.hide()

      #install_pkg_are_you_sure_dialog =\
      #  self.all_widgets.get_widget('install_pkg_are_you_sure_dialog')
      #self.current_dialog = install_pkg_are_you_sure_dialog

      #install_are_you_sure_label =\
      #  self.all_widgets.get_widget('install_are_you_sure_label')
      #
      #label_text = ''
      #pkgs = []
      #for pathname in path_list:
      #  index = pathname.rfind('/')

      #  pkg = pathname[index+1:]
      #  pkg = pkg[:pkg.find('.')]
      #  pkg = pkg[:pkg.rfind('-')]

      #  pkgs.append(pkg)

      #  if label_text == '':
      #    label_text = pkg
      #  else:
      #    label_text = label_text + pkg + '\n'

      #install_are_you_sure_label.set_text(label_text)

      #self.current_dialog_on = True
      #response = install_pkg_are_you_sure_dialog.run()
      #install_pkg_are_you_sure_dialog.hide()
      #self.current_dialog_on = False

      if response == gtk.RESPONSE_OK:
        #self.busy_dialog = self.all_widgets.get_widget('busy_dialog')
        self.busy_dialog = self.all_widgets.get_widget('busy_dialog2')
        self.busy_cancel_button =\
        self.all_widgets.get_widget('busy_cancel_button')
        #self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar3')
        self.busy_progress_bar3 =\
        self.all_widgets.get_widget('busy_progress_bar4')
        self.busy_progress_bar3.set_text('')
        self.busy_progress_bar3.set_fraction(0.0)
        self.busy_dialog.show_now()

        self.fraction_increment = 1.0 / (4 + 2 * len(path_list))
        self.current_fraction = 0.0

        selection = self.treeview.get_selection()
        treemodel, iter = selection.get_selected()

        # Step 1: create a new transaction
        self.trans = self.shell.alpm_transaction_init(alpm.PM_TRANS_TYPE_UPGRADE,
            0, self.gui_trans_cb_ev, self.gui_trans_cb_conv)

        # add targets to it
        for path in path_list:
          try:
            self.shell.alpm_transaction_add_target(path)
          except alpm.PackageNotFoundTransactionException, inst:
            print inst
            self.shell.alpm_transaction_release()
            self.busy_dialog.hide()
            return
        # Step 2: compute the transaction
        self.alpm_run_in_thread_and_wait(self.shell.alpm_transaction_prepare, {})
        if self.cancel_operation:
          self.shell.alpm_transaction_release()
          self.busy_dialog.hide()
          return
        if self.shell.last_exception:
          if self.shell.last_exception[0] == 1:
            depmiss_list = self.shell.last_exception[1]

            conflicts_error_dialog =\
              self.all_widgets.get_widget('conflicts_error_dialog')
            conflicts_error_label =\
              self.all_widgets.get_widget('conflicts_error_label')

            for depmiss in depmiss_list.args[0]:
              str = self.alpm_depmiss_to_str(depmiss)
              conflicts_error_label.set_text(str)

            conflicts_error_dialog.run()
            conflicts_error_dialog.hide()

            self.shell.alpm_transaction_release()
            self.busy_dialog.hide()
            return
          elif self.shell.last_exception[0] == 2:
            conflict_list = self.shell.last_exception[1]
            conflicts_error_dialog =\
              self.all_widgets.get_widget('conflicts_error_dialog')
            conflicts_error_label =\
              self.all_widgets.get_widget('conflicts_error_label')

            str = ''
            for conflict in conflict_list.args[0]:
              str = str + ('%s: conflicts with %s' % (conflict.get_target(),
                conflict.get_name()))

            conflicts_error_label.set_text(str)

            conflicts_error_dialog.run()
            conflicts_error_dialog.hide()

            self.shell.alpm_transaction_release()
            self.busy_dialog.hide()
            return
          elif self.shell.last_exception[0] == 4:
            conflict_list = self.shell.last_exception[1]
            conflicts_error_dialog =\
              self.all_widgets.get_widget('conflicts_error_dialog')
            conflicts_error_label =\
              self.all_widgets.get_widget('conflicts_error_label')

            str = ''
            for conflict in conflict_list.args[0]:
              conf_type = conflict.get_type()

              if conf_type == alpm.PM_CONFLICT_TYPE_TARGET:
                str = str + '%s exists in \"%s\" (target) and \" %s\" (target)\n' %\
                    (conflict.get_file(), conflict.get_target(),
                        conflict.get_conflict_target())
              elif conf_type == alpm.PM_CONFLICT_TYPE_FILE:
                str = str + '%s: %s exists in filesystem\n' % (conflict.get_target(),
                    conflict.get_file())
            
            conflicts_error_label.set_text(str)
            conflicts_error_dialog.run()
            conflicts_error_dialog.hide()

            self.shell.alpm_transaction_release()
            self.busy_dialog.hide()
            return

        # Step 3: actually perform the installation
        self.alpm_run_in_thread_and_wait(self.shell.alpm_transaction_commit, {})
        if self.cancel_operation:
          self.shell.alpm_transaction_release()
          self.busy_dialog.hide()
          return
        if self.shell.last_exception:
          if self.shell.last_exception[0] == 3:

            inst = self.shell.last_exception[1]
            conflicts_error_dialog =\
              self.all_widgets.get_widget('conflicts_error_dialog')
            conflicts_error_label =\
              self.all_widgets.get_widget('conflicts_error_label')

            conflicts_error_label.set_text(inst.args[0])

            conflicts_error_dialog.run()
            conflicts_error_dialog.hide()

            self.shell.alpm_transaction_release()
            self.busy_dialog.hide()
            return
          else:
            self.shell.alpm_transaction_release()
            self.busy_dialog.hide()
        else:
          self.shell.alpm_transaction_release()
          self.busy_dialog.hide()
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

  # def alpm_is_group(self, name): {{{
  def alpm_is_group(self, name):
    return name in self.local_groups or name in self.groups
  # }}}

  # def on_cursor_changed(self, treeview): {{{
  def on_cursor_changed(self, treeview):
    bool_col = 0
    name_col = 1

    selection = treeview.get_selection()
    treemodel, iter = selection.get_selected()
    info = ''
    if not iter:
      return 

    if treeview == self.treeview:
      bool_col = 1
      name_col = 0

      (tuple, column) = treeview.get_cursor()

      if not column:
        return
      renderers = column.get_cell_renderers()

      # don't show a popup if the column is a CellRendererToggle
      if type(renderers[0]) is gtk.CellRendererToggle:
        return

      # treeview of pkgs
      name = treemodel.get_value(iter, name_col)

      buffer = gtk.TextBuffer()
      
      if not self.alpm_is_group(name):
        try:
          info = self.local_pkg_info[name]
        except KeyError:
          info = self.shell.alpm_local_info(name)
          self.local_pkg_info[name] = info
        
        if info == None:
          try:
            remote_info = self.remote_pkg_info[name]
          except KeyError:
            selection_repos = self.treeview_repos.get_selection()
            treemodel_repos, iter_repos = selection_repos.get_selected()

            if iter_repos:
              repo_name = treemodel_repos.get_value(iter_repos, 0).lower()
              remote_info = self.shell.alpm_info(name, repo_name)
            else:
              # FIXME: what about if 'name' isn't installed????
              remote_info = self.shell.alpm_info(name)

            self.remote_pkg_info[name] = remote_info

          self.__add_pkg_info_markuped_to_text_buffer__(buffer, remote_info,\
              installed = False)
        else:
          self.__add_pkg_info_markuped_to_text_buffer__(buffer, info)
        self.information_text.set_buffer(buffer)
      else: # group
        installed = True
        info = self.shell.alpm_group_local_info(name)
        if not info:
          installed = False
          info = self.shell.alpm_group_info(name)

        self.__add_pkg_info_markuped_to_text_buffer__(buffer, info,\
            installed)
        self.information_text.set_buffer(buffer)

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
    #gobject.source_remove(self.timer)
    self.timer = 0
    self.shell.release()
    gtk.main_quit()
    return False
  # }}}

  # def on_destroy(self, widget, data=None): {{{
  def on_destroy(self, widget, data=None):
    if widget == self.main_window:
      #gobject.source_remove(self.timer)
      self.timer = 0
      gtk.main_quit()
      del self.th
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
    self.shell.release()
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
    self.upgrades = None
    if button == self.update_db:
      self.init_transaction = False

      #self.busy_dialog = self.all_widgets.get_widget('busy_dialog')
      self.busy_dialog = self.all_widgets.get_widget('busy_dialog2')
      self.busy_cancel_button =\
      self.all_widgets.get_widget('busy_cancel_button')
      #self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar3')
      self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar4')
      #self.busy_status_label = self.all_widgets.get_widget('busy_status_label')
      self.busy_status_label = self.all_widgets.get_widget('busy_status_label2')
      self.busy_progress_bar3.set_text('')
      self.current_fraction = 0.0
      self.fraction_increment = 1 / (1.0 + (2.0 * 2.0))
      #self.busy_progress_bar3.set_fraction(0.0)
      self.busy_dialog.show_now()

      self.current_fraction = self.current_fraction + self.fraction_increment
      print 'frac: ', self.current_fraction
      gobject.idle_add(self.alpm_progress_bar_set_text_and_fraction,\
          self.busy_progress_bar3, 'Downloading databases...',\
          False, self.current_fraction)

      # update the databases {{{
      if not skip_update_db:
        upgrades = []
        missed_deps = []
        self.init_transaction = True

        self.alpm_run_in_thread_and_wait(self.shell.alpm_refresh_dbs,
            {'report_hook': self.alpm_urllib_report_hook,
              'cancel_cb':  self.cancel_cb})
        if self.cancel_operation:
          if self.shell.trans:
            self.shell.alpm_transaction_release()
          self.busy_dialog.hide()
          return

        self.busy_status_label.set_markup('<i>Please wait...</i>')
        self.alpm_run_in_thread_and_wait(self.shell.alpm_update_databases,\
            {'flags': 0, 'cb_ev': self.gui_trans_cb_ev,\
            'cb_conv': self.gui_trans_cb_conv})
        if self.cancel_operation:
          self.shell.alpm_transaction_release()
          self.busy_dialog.hide()
          return

        if self.shell.last_exception and self.shell.last_exception[0]:
          # TODO: present a nice dialog
          if self.shell.last_exception[0] == 1:
            print self.shell.last_exception[1]
            self.busy_dialog.hide()
            self.shell.alpm_transaction_release()
            return
          elif self.shell.last_exception[0] == 2:
            print self.shell.last_exception[1]
            self.busy_dialog.hide()
            self.shell.alpm_transaction_release()
            return
        else:
          (upgrades, missed_deps) = self.shell.get_prev_return()
          print "GUI: upgrades: ", upgrades
          print "GUI: missed_deps: ", missed_deps
          self.upgrades = upgrades
          self.busy_dialog.hide()

          self.update_db_popup = self.all_widgets.get_widget('update_db_popup')
          self.current_dialog = self.update_db_popup
          self.current_dialog_on = True
          response = self.update_db_popup.run()

          self.update_db_popup.hide()
          self.current_dialog_on = False
          #self.shell.alpm_transaction_release()
      # }}}

      # check if pacman is in the upgrades and install it {{{
      if self.shell.alpm_check_if_pkg_in_pkg_list('pacman', upgrades):
        pacman_upgrade_dialog =\
          self.all_widgets.get_widget('pacman_upgrade_dialog')
        self.current_dialog = pacman_upgrade_dialog
        
        self.current_dialog_on = True
        response = pacman_upgrade_dialog.run()
        pacman_upgrade_dialog.hide()
        self.current_dialog_on = False
        
        if response == gtk.RESPONSE_OK:
          self.shell.start_timer()
          self.alpm_install_targets(['pacman'])
          self.try_sem_animate_progress_bar()

          self.on_update_db_clicked(button, True)
      # }}}

      # setup the dialog querying the user for packages to install {{{
      #fresh_updates_dialog = self.all_widgets.get_widget('fresh_updates_dialog2')
      fresh_updates_dialog = self.all_widgets.get_widget('fresh_updates_dialog3')
      self.current_dialog = fresh_updates_dialog
      fresh_updates_label = self.all_widgets.get_widget('fresh_updates_label')

      #fresh_updates_treeview =\
      #  self.all_widgets.get_widget('fresh_updates_treeview')
      fresh_updates_treeview =\
        self.all_widgets.get_widget('fresh_updates_treeview2')
      #l = gtk.ListStore('gboolean', 'gchararray', 'gchararray')
      l = gtk.ListStore('gchararray', 'gboolean', 'gchararray')

      textrenderer = gtk.CellRendererText()
      togglerenderer = gtk.CellRendererToggle()
      togglerenderer.set_active(True)

      togglerenderer.connect('toggled', self.toggled, l, 1)

      if fresh_updates_treeview.get_columns() == []:
        selectedcolumn = gtk.TreeViewColumn('')
        #selectedcolumn.set_sort_column_id(0)
        selectedcolumn.pack_start(togglerenderer)
        selectedcolumn.set_attributes(togglerenderer, active=1)
        selectedcolumn.set_clickable(True)
        selectedcolumn.connect('clicked', self.on_treeview_column_clicked, l,\
            1)
        
        namecolumn = gtk.TreeViewColumn('Name', textrenderer, markup=2)
        namecolumn.set_resizable(True)
        #namecolumn.set_min_width(300)
        #namecolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        namecolumn.set_sort_column_id(0)
        #namecolumn.pack_start(textrenderer)
        #namecolumn.set_attributes(textrenderer, text=1)

        #repocolumn = gtk.TreeViewColumn('Repository')
        ##repocolumn.set_sort_column_id(2)
        #repocolumn.pack_start(textrenderer)
        #repocolumn.set_attributes(textrenderer, text=2)
        invisiblecolumn = gtk.TreeViewColumn('', None)
        invisiblecolumn.set_visible(False)

        fresh_updates_treeview.append_column(invisiblecolumn)
        fresh_updates_treeview.append_column(selectedcolumn)
        fresh_updates_treeview.append_column(namecolumn)
        #fresh_updates_treeview.append_column(repocolumn)
      # }}}

      if upgrades != []:
        import cgi
        for update in upgrades:
          pkg = update.get_package()
          pkg_name = cgi.escape(pkg.get_name())
          pkg_ver = cgi.escape(pkg.get_version())
          pkg_desc = pkg.get_description()

          #if len(pkg_desc) > 40:
          #  pkg_desc = pkg_desc[:40]
          #  pkg_desc+= '...'
          pkg_desc = cgi.escape(pkg_desc)
          repo = pkg.get_database().get_tree_name()

          #print 'name \'%s\' ver \'%s\' \'%s\'' % (pkg_name, pkg_ver, pkg_desc)
          text = '<b>%s</b> - %s - <i>%s</i>\n<i>%s</i>' % (pkg_name, pkg_ver,\
              repo, pkg_desc)
          #text = cgi.escape(text)
          #print 'appending \'%s\'' % text
          #l.append([False, text, repo])
          l.append([pkg_name, False, text])
        
        fresh_updates_treeview.set_model(l)

        self.current_dialog_on = True
        response = fresh_updates_dialog.run()
        fresh_updates_dialog.hide()
        self.current_dialog_on = False
        
        fresh_updates_installed = False
        
        if response == gtk.RESPONSE_OK:
          if self.init_transaction:
            self.init_transaction = False

          upgrades = self.get_all_selected_packages(l, boolean_col=1, name_col=0)

          self.shell.alpm_transaction_release()
          self.busy_status_label.set_markup('<i>Please wait...</i>')
          if missed_deps == None:
            ret = self.alpm_install_targets(upgrades)
          else:
            ret = self.alpm_install_targets(upgrades + missed_deps)

          if ret:
            updates_text = ''

            for upgrade in upgrades:
              updates_text = updates_text + ' ' + upgrade
            fresh_updates_installed = True  
          else:
            return
        else:
          if self.init_transaction:
            self.shell.alpm_transaction_release()
            self.init_transaction = False
          return

        updates = upgrades
        # TODO: is this necessary?
        for pkg_name in updates:
          info = self.shell.alpm_info(pkg_name)
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
        no_upgrades_dialog =\
          self.all_widgets.get_widget('no_upgrades_dialog')
        no_upgrades_dialog.run()
        no_upgrades_dialog.hide()

      if self.init_transaction:
        self.init_transaction = False
      self.busy_status_label.set_markup('<i>Please wait...</i>')
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

  # def alpm_get_number_of_packages_to_download(self, targets): {{{
  def alpm_get_number_of_packages_to_download(self, targets):
    root_dir = self.shell.alpm.get_root()
    cache_dir = self.shell.alpm.get_cache_dir()
    ldir = root_dir + cache_dir
    
    number = 0
    for pkg_name in targets:
      (_, pkg_ver) = self.shell.alpm_get_pkg_repo(pkg_name)
      
      path = ldir + '/' + pkg_name + '-' + pkg_ver + alpm.PM_EXT_PKG

      try:
        os.stat(path)
      except OSError:
        # file is not in the cache dir
        number = number + 1
    return number
  # }}}

  # def alpm_install_targets(self, targets, repo = None): {{{
  def alpm_install_targets(self, targets, repo = None):
    # TODO: check if there's something searched for or a repo selected, and
    # update the pkg_treeview accordingly
    self.busy_status_label = self.all_widgets.get_widget('busy_status_label2')
    number_pkgs_to_download =\
      self.alpm_get_number_of_packages_to_download(targets)

    # TODO: figure this out, for good
    self.fraction_increment = 1.0 / (6 + 2 * len(targets))
    self.current_fraction = 0.0

    pkg_are_you_sure_dialog =\
      self.all_widgets.get_widget('pkg_are_you_sure_dialog2')

    self.are_you_sure_treeview =\
        self.all_widgets.get_widget('pkgs_treeview')

    liststore = gtk.ListStore('gchararray')

    cols = self.are_you_sure_treeview.get_columns()
    if cols == []:
      textrenderer = gtk.CellRendererText()

      namecolumn = gtk.TreeViewColumn('Name')
      namecolumn.set_resizable(True)
      namecolumn.set_min_width(300)
      namecolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
      namecolumn.set_sort_column_id(0)
      namecolumn.pack_start(textrenderer)
      namecolumn.set_attributes(textrenderer, text=0)

      self.are_you_sure_treeview.append_column(namecolumn)

    are_you_sure_message_label =\
        self.all_widgets.get_widget('are_you_sure_message_label')

    are_you_sure_message_label.set_text(\
        'Do you wish to install these packages?')

    for target in targets:
      liststore.append([target])

    liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)

    self.are_you_sure_treeview.set_model(liststore)

    response = pkg_are_you_sure_dialog.run()
    pkg_are_you_sure_dialog.hide()

    if response == gtk.RESPONSE_CANCEL:
      return False

    #self.busy_dialog = self.all_widgets.get_widget('busy_dialog')
    self.busy_dialog = self.all_widgets.get_widget('busy_dialog2')
    self.busy_cancel_button =\
    self.all_widgets.get_widget('busy_cancel_button')
    #self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar3')
    self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar4')
    self.busy_progress_bar3.set_text('')
    self.busy_progress_bar3.set_fraction(0.0)
    self.busy_dialog.show_now()

    # Step 1: create a new transaction
    self.trans = self.shell.alpm_transaction_init(alpm.PM_TRANS_TYPE_SYNC, 0,
        self.gui_trans_cb_ev, self.gui_trans_cb_conv)

    # process targets and add them to the transaction
    for pkg_name in targets:
      ret = self.shell.alpm_transaction_add_target(pkg_name)
      if not ret:
        self.shell.alpm_transaction_release()
        self.busy_dialog.hide()
        return False

    # Step 2: compute the transaction
    #try:
    self.alpm_run_in_thread_and_wait(self.shell.alpm_transaction_prepare, {})
    if self.cancel_operation:
      self.shell.alpm_transaction_release()
      self.busy_dialog.hide()
      return
    if self.shell.last_exception:
      if self.shell.last_exception[0] == 1:
        # alpm.UnsatisfiedDependenciesTransactionException
        depmiss_list = self.shell.last_exception[1]
        unsatisfied_dependencies_dialog = \
            self.all_widgets.get_widget('unsatisfied_dependencies_dialog')
        unsatisfied_dependencies_textview = \
            self.all_widgets.get_widget('unsatisfied_dependencies_textview')

        buffer = gtk.TextBuffer()

        unsatisfied_dependencies_textview.set_buffer(buffer)

        depmiss_names = []
        for depmiss in depmiss_list.args[0]:
          depmiss_names.append(depmiss.get_name())
          buffer.insert_at_cursor(self.alpm_depmiss_to_str(depmiss) + '\n')

        response = unsatisfied_dependencies_dialog.run()
        unsatisfied_dependencies_dialog.hide()

        self.shell.alpm_transaction_release()

        if response == gtk.RESPONSE_OK:
          self.alpm_install_targets(targets + depmiss_names)
        else:
          self.busy_dialog.hide()
        return
      elif self.shell.last_exception[0] == 2:
        # alpm.ConflictingFilesTransactionException
        conflict_list = self.shell.last_exception[1]
        conflicts_error_dialog =\
          self.all_widgets.get_widget('conflicts_error_dialog')
        conflicts_error_label =\
          self.all_widgets.get_widget('conflicts_error_label')

        string = ''
        for conflict in conflict_list.args[0]:
          string = string + ('%s: conflicts with %s' % (conflict.get_target(),
            conflict.get_name()))

        conflicts_error_label.set_text(string)

        conflicts_error_dialog.run()
        conflicts_error_dialog.hide()

        self.shell.alpm_transaction_release()
        self.busy_dialog.hide()
        return False
      elif self.shell.last_exception[0] == 4:
        # alpm.ConflictingFilesTransactionException
        conflict_list = self.shell.last_exception[1]

        conflicts_error_dialog =\
          self.all_widgets.get_widget('conflicts_error_dialog')
        conflicts_error_label =\
          self.all_widgets.get_widget('conflicts_error_label')

        string = ''
        for conflict in conflict_list.args[0]:
          conf_type = conflict.get_type()

          if conf_type == alpm.PM_CONFLICT_TYPE_TARGET:
            string = string + '%s exists in \"%s\" (target) and \" %s\" (target)\n' %\
                (conflict.get_file(), conflict.get_target(),
                    conflict.get_conflict_target())
          elif conf_type == alpm.PM_CONFLICT_TYPE_FILE:
            string = string + '%s: %s exists in filesystem\n' % (conflict.get_target(),
                conflict.get_file())

        conflicts_error_label.set_text(string)
        conflicts_error_dialog.run()
        conflicts_error_dialog.hide()

        self.shell.alpm_transaction_release()
        self.busy_dialog.hide()
        return False

    self.busy_dialog.show_all()
    packages = self.shell.alpm_transaction_get_sync_packages()
    if packages == []:
      # TODO: use a dialog for the following print
      #print 'No packages to install/remove'
      self.shell.alpm_transaction_release()
      self.busy_dialog.hide()
      return

    #print 'PACKAGES IN THE TRANSACTION: ', packages
    to_remove = []
    to_install = []
    # list targets and get confirmation
    for sync in packages:
      pkg = sync.get_package()
      if sync.get_type() == alpm.PM_SYNC_TYPE_REPLACE:
        # replace
        data = sync.get_data()
        for pkg2 in data:
          pkg_name = pkg2.get_name()
          pkg_ver = pkg2.get_version()
          #if pkg_name not in to_remove:
          tuple = (pkg_name, pkg_ver)
          if tuple not in to_remove:
            to_remove.append(tuple)

      pkgname = pkg.get_name()
      pkgver = pkg.get_version()
      pkg_desc = pkg.get_description()
      #string = '%s-%s-%s' % (pkgname, pkgver, pkg_desc)
      string = '%s-%s' % (pkgname, pkgver)
      to_install.append(string)

    depends = []
    for spkg in packages:
      if spkg.get_type() == alpm.PM_SYNC_TYPE_DEPEND:
        depends.append(spkg.get_package().get_name())

    tmp = len(targets) + len(depends)
    old_increment = self.fraction_increment
    self.fraction_increment = 1.0 / (6 + (2 * tmp))
    self.current_fraction = self.current_fraction - ((tmp - len(targets)) *
        self.fraction_increment)

    self.busy_progress_bar3.set_fraction(self.current_fraction)

    install_remove_pkgs_dialog =\
      self.all_widgets.get_widget('install_remove_pkgs_dialog2')

    install_remove_treeview =\
      self.all_widgets.get_widget('install_remove_treeview2')

    if install_remove_treeview.get_columns() == []:
      textrenderer = gtk.CellRendererText()
      namecolumn = gtk.TreeViewColumn('Name', textrenderer, markup=0)
      namecolumn.set_resizable(True)
      namecolumn.set_min_width(300)
      namecolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

      install_remove_treeview.append_column(namecolumn)
    #store = gtk.ListStore(str)
    store = gtk.TreeStore(str)
    
    import cgi
    print 'INSTALL REMOVE'
    # only available in 2.10, tooltips per treeview row
    #install_remove_tips = gtk.Tooltips()
    to_remove_iter = store.append(None, ['<big><b>Remove</b></big>'])
    for (pkg_name, pkg_ver) in to_remove:
      pkg_name = cgi.escape(pkg_name)
      pkg_ver = cgi.escape(pkg_ver)
      text = '<b>%s</b>\n%s' % (pkg_name, pkg_ver)
      #text = '<b>%s</b>'% pkg_name
      treeiter = store.append(to_remove_iter, [text])
      #install_remove_tips.set_tip(treeiter, pkg_name)

    to_install_iter = store.append(None, ['<big><b>Install</b></big>'])
    for pkg_str in to_install:
      pkg_str2 = pkg_str[:pkg_str.rindex('-')]
      pkg_desc = pkg_str2[pkg_str2.rindex('-')+1:]

      pkg_name = pkg_str2[:pkg_str2.rindex('-')]
      pkg_name = cgi.escape(pkg_name)
      pkg_ver = pkg_str[pkg_str[:pkg_str.rindex('-')].rindex('-')+1:]
      #pkg_ver = pkg_str2[pkg_str2.rindex('-')+1:]
      pkg_ver = cgi.escape(pkg_ver)

      text = '<b>%s</b>\n%s' % (pkg_name, pkg_ver)
      treeiter = store.append(to_install_iter, [text])
      #install_remove_tips.set_tip(treeiter, pkg_desc)

    #install_remove_tips.enable()

    install_remove_treeview.set_model(store)
    install_remove_treeview.expand_all()

    # BACKUP {{{
    #install_remove_pkgs_dialog =\
    #  self.all_widgets.get_widget('install_remove_pkgs_dialog')
    #to_remove_label = self.all_widgets.get_widget('to_remove_label')
    #to_install_label = self.all_widgets.get_widget('to_install_label')

    #to_remove_treeview = self.all_widgets.get_widget('to_remove_treeview')
    #to_install_treeview = self.all_widgets.get_widget('to_install_treeview')

    #if to_remove_treeview.get_columns() == [] and\
    #    to_install_treeview.get_columns() == []:
    #  textrenderer = gtk.CellRendererText()
    #  namecolumn = gtk.TreeViewColumn('Name')
    #  namecolumn.set_sort_column_id(0)
    #  namecolumn.pack_start(textrenderer)
    #  namecolumn.set_attributes(textrenderer, text=0)
    #  
    #  namecolumn2 = gtk.TreeViewColumn('Name')
    #  namecolumn2.set_sort_column_id(0)
    #  namecolumn2.pack_start(textrenderer)
    #  namecolumn2.set_attributes(textrenderer, text=0)

    #  versioncolumn = gtk.TreeViewColumn('Version')
    #  versioncolumn.set_sort_column_id(1)
    #  versioncolumn.pack_start(textrenderer)
    #  versioncolumn.set_attributes(textrenderer, text=1)

    #  versioncolumn2 = gtk.TreeViewColumn('Version')
    #  versioncolumn2.set_sort_column_id(1)
    #  versioncolumn2.pack_start(textrenderer)
    #  versioncolumn2.set_attributes(textrenderer, text=1)

    #  to_remove_treeview.append_column(namecolumn)
    #  to_remove_treeview.append_column(versioncolumn)
    #  to_install_treeview.append_column(namecolumn2)
    #  to_install_treeview.append_column(versioncolumn2)

    #to_remove_liststore = gtk.ListStore('gchararray', 'gchararray')
    #to_install_liststore = gtk.ListStore('gchararray', 'gchararray')

    ## fill to_remove_treeview
    #for (pkg_name, pkg_ver) in to_remove:
    #  to_remove_liststore.append([pkg_name, pkg_ver])

    ## fill to_install_treeview
    #for pkg_str in to_install:
    #  #print 'PKG_STR: <%s> '  % pkg_str
    #  pkg_str2 = pkg_str[:pkg_str.rindex('-')]

    #  pkg_name = pkg_str2[:pkg_str2.rindex('-')]
    #  pkg_ver = pkg_str[pkg_str[:pkg_str.rindex('-')].rindex('-')+1:]
    #  to_install_liststore.append([pkg_name, pkg_ver])

    #to_remove_treeview.set_model(to_remove_liststore)
    #to_install_treeview.set_model(to_install_liststore)
    # }}}

    response = install_remove_pkgs_dialog.run()
    install_remove_pkgs_dialog.hide()

    if response == gtk.RESPONSE_CANCEL:
      self.busy_dialog.hide()
      return False

    # group sync records by repository and download
    root_dir = self.shell.alpm.get_root()
    cache_dir = self.shell.alpm.get_cache_dir()
    ldir = root_dir + cache_dir
    
    pmc_syncs = self.shell.alpm_get_pmc_syncs()

    files = []
    if not repo:
      for pmc_sync in pmc_syncs:
        dbname = pmc_sync['db'].get_tree_name()

        for sync in packages:
          pkg = sync.get_package()
          pkg_db = pkg.get_database()
          pkg_db_name = pkg_db.get_tree_name()

          if dbname == pkg_db_name:
            pkg_name = pkg.get_name()
            pkg_ver = pkg.get_version()

            path = ldir + '/' + pkg_name + '-' + pkg_ver + alpm.PM_EXT_PKG

            try:
              os.stat(path)
            except OSError:
              # file is not in the cache dir, so add it to the list
              files.append(path)
    else:
      dbname = repo
      for sync in packages:
        pkg = sync.get_package()
        pkg_db = pkg.get_database()
        pkg_db_name = pkg_db.get_tree_name()

        if dbname == pkg_db_name:
          pkg_name = pkg.get_name()
          pkg_ver = pkg.get_version()

          path = ldir + '/' + pkg_name + '-' + pkg_ver + alpm.PM_EXT_PKG

          try:
            os.stat(path)
          except OSError:
            # file is not in the cache dir, so add it to the list
            files.append(path)

    cleanup = False
    #print 'FILES:', files
    packages = self.shell.alpm_transaction_get_sync_packages()

    if files != []:
      # download stuff
      self.busy_progress_bar3.set_text('Retrieving packages from %s...' %
          dbname)
      if not os.stat(ldir):
        # no cache directory, make it
        try:
          os.makedirs(ldir)
        except Error:
          # failed to make the dir, fall back to /tmp and unlink the pkg
          # afterwards
          ldir = '/tmp'
          alpm.set_cache_dir(ldir)
          cleanup = True
      
      self.downloading_db = False
      kwargs = {'files': files, 'progress_bar': self.busy_progress_bar3,\
        'report_hook': self.alpm_urllib_report_hook}
      self.alpm_run_in_thread_and_wait(self.shell.alpm_download_packages,
          kwargs)
      if self.cancel_operation:
        self.shell.alpm_transaction_release()
        self.busy_dialog.hide()
        return
      filenames = self.shell.get_prev_return()
      print 'DONE DOWNLOADING: ', filenames
      self.busy_status_label.set_markup('<i>Please wait...</i>')
      
      self.downloading_db = True
      files = []

    # check integrity of the files
    bail = False

    conflicts_error_dialog =\
      self.all_widgets.get_widget('conflicts_error_dialog')
    conflicts_error_label =\
      self.all_widgets.get_widget('conflicts_error_label')

    string = ''
    for sync in packages:
      pkg = sync.get_package()
      try:
        pkg.check_md5sum()
      except alpm.PackageCorruptedException:
        #print 'archive %s is corrupted' % pkg.get_name()
        string = string + ('archive %s is corrupted\n' % pkg.get_name())

        bail = True
      except Exception, inst:
        string = string + ('could not get checksum for package %s (%s)\n'\
            % (pkg.get_name(), inst))
        
        bail = True
        
    if bail:
      conflicts_error_dialog.run()
      conflicts_error_dialog.hide()
      self.busy_dialog.hide()

      self.shell.alpm_transaction_release()
      return
    #else:
      #del conflicts_error_dialog
      #del conflicts_error_label

    # Step 3: actually perform the installation
    #try:
      #self.shell.alpm_transaction_commit()
    self.alpm_run_in_thread_and_wait(self.shell.alpm_transaction_commit, {})
    if self.cancel_operation:
      self.shell.alpm_transaction_release()
      self.busy_dialog.hide()
      return

    #except alpm.ConflictingFilesTransactionException, conflict_list:
    if self.shell.last_exception:
      if self.shell.last_exception[0] == 4:
        # alpm.ConflictingFilesTransactionException
        conflict_list = self.shell.last_exception[1]
        conflicts_error_dialog =\
          self.all_widgets.get_widget('conflicts_error_dialog')
        conflicts_error_label =\
          self.all_widgets.get_widget('conflicts_error_label')

        string = ''
        for conflict in conflict_list.args[0]:
          conf_type = conflict.get_type()
          if conf_type == alpm.PM_CONFLICT_TYPE_TARGET:
            string = string + ("%s exists in \"%s\" (target) and \"%s\" (target)\n" %\
                (conflict.get_file(), conflict.get_target(),\
                    conflict.get_conflict_target()))
          elif conf_type == alpm.PM_CONFLICT_TYPE_FILE:
            string = string + ("%s: %s exists in filesystem\n"\
                % (conflict.get_target(), conflict.get_conflict_target()))

        conflicts_error_label.set_text(string)
        conflicts_error_dialog.run()
        conflicts_error_dialog.hide()
        self.busy_dialog.hide()

        print 'RELEASE 1'
        self.shell.alpm_transaction_release()

        if cleanup:
          for f in files:
            os.unlink(f)
        return False
      #except RuntimeError, inst:
      elif self.shell.last_exception[0] == 3:
        # RuntimeError
        conflicts_error_dialog =\
          self.all_widgets.get_widget('conflicts_error_dialog')
        conflicts_error_label =\
          self.all_widgets.get_widget('conflicts_error_label')

        conflicts_error_label.set_text(inst.args[0])

        conflicts_error_dialog.run()
        conflicts_error_dialog.hide()
        self.busy_dialog.hide()

        print 'RELEASE 2'
        self.shell.alpm_transaction_release()
        if cleanup:
          for f in files:
            os.unlink(f)
        return False

    list = [syncpkg.get_package().get_name() for syncpkg in packages]

    #print 'packages installed: ', list

    self.__add_pkg_info_to_local_pkgs__(list)
    self.refresh_pkgs_treeview()
    self.busy_dialog.hide()

    print 'RELEASE 3'
    self.shell.alpm_transaction_release()
    if cleanup:
      for f in files:
        os.unlink(f)
    return True
  # }}}

  # def on_install_pkg_clicked(self, button): {{{
  def on_install_pkg_clicked(self, button):
    pkgs_to_install = self.get_all_selected_packages(self.liststore, 1, 0)

    if pkgs_to_install == []:
      return 

    self.alpm_install_targets(pkgs_to_install)

  # }}}

  # def alpm_remove_targets(self, targets): {{{
  def alpm_remove_targets(self, targets):
    # TODO: check if there's something searched for or a repo selected, and
    # update the pkg_treeview accordingly
    # TODO: figure this out, for good
    self.fraction_increment = (1.0 / (2 + 2 * len(targets)))
    self.current_fraction = 0.0

    pkg_are_you_sure_dialog =\
      self.all_widgets.get_widget('pkg_are_you_sure_dialog2')

    self.are_you_sure_treeview =\
        self.all_widgets.get_widget('pkgs_treeview')

    liststore = gtk.ListStore('gchararray')
    textrenderer = gtk.CellRendererText()

    cols = self.are_you_sure_treeview.get_columns()
    if cols == []:
      namecolumn = gtk.TreeViewColumn('Name')
      namecolumn.set_resizable(True)
      namecolumn.set_min_width(300)
      namecolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
      namecolumn.set_sort_column_id(0)
      namecolumn.pack_start(textrenderer)
      namecolumn.set_attributes(textrenderer, text=0)

      self.are_you_sure_treeview.append_column(namecolumn)

    are_you_sure_message_label =\
        self.all_widgets.get_widget('are_you_sure_message_label')

    are_you_sure_message_label.set_text(\
        'Do you wish to remove these packages?')

    for pkg_name in targets:
      liststore.append([pkg_name])

    liststore.set_sort_column_id(0, gtk.SORT_ASCENDING)

    self.are_you_sure_treeview.set_model(liststore)

    self.current_dialog_on = True
    response = pkg_are_you_sure_dialog.run()
    pkg_are_you_sure_dialog.hide()
    
    self.current_dialog_on = False

    if response == gtk.RESPONSE_CANCEL:
      return
    else:
      #self.busy_dialog = self.all_widgets.get_widget('busy_dialog')
      self.busy_dialog = self.all_widgets.get_widget('busy_dialog2')
      self.busy_cancel_button =\
      self.all_widgets.get_widget('busy_cancel_button')
      #self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar3')
      self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar4')
      self.busy_progress_bar3.set_text('')
      self.busy_progress_bar3.set_fraction(0.0)
      self.busy_dialog.show_now()
      # Step 1: create a new transaction
      self.trans = self.shell.alpm_transaction_init(alpm.PM_TRANS_TYPE_REMOVE,
          0, self.gui_trans_cb_ev, self.gui_trans_cb_conv)

      # and add targets to it
      for pkg_name in targets:
        ret = self.shell.alpm_transaction_add_target(pkg_name)
        if not ret:
          self.shell.alpm_transaction_release()
          self.busy_dialog.hide()
          return

      # Step 2: prepare the transaction
      self.alpm_run_in_thread_and_wait(self.shell.alpm_transaction_prepare,{})
      if self.cancel_operation:
        self.shell.alpm_transaction_release()
        self.busy_dialog.hide()
        return
      if self.shell.last_exception:
        if self.shell.last_exception[0] == 1:
          # alpm.UnsatisfiedDependenciesTransactionException
          depmiss_list = self.shell.last_exception[1]
          conflicts_error_dialog =\
            self.all_widgets.get_widget('conflicts_error_dialog')
          conflicts_error_label =\
            self.all_widgets.get_widget('conflicts_error_label')

          string = ''
          for depmiss in depmiss_list.args[0]:
            #string = string + self.alpm_depmiss_to_str(depmiss) + '\n'
            string = string + ('%s is required by %s' % (depmiss.get_target(),
              depmiss.get_name()))
          
          conflicts_error_label.set_text(string)
          conflicts_error_dialog.run()
          conflicts_error_dialog.hide()
          
          self.shell.alpm_transaction_release()
          self.busy_dialog.hide()
          self.shell.last_exception = None
          return
        elif self.shell.last_exception[0] == 3:
          # RuntimeError
          inst = self.shell.last_exception[1]
          conflicts_error_dialog =\
            self.all_widgets.get_widget('conflicts_error_dialog')
          conflicts_error_label =\
            self.all_widgets.get_widget('conflicts_error_label')

          string = inst.args[0]

          conflicts_error_label.set_text(string)
          conflicts_error_dialog.run()
          conflicts_error_dialog.hide()
          
          self.shell.alpm_transaction_release()
          self.busy_dialog.hide()
          self.shell.last_exception = None
          return

      #t = self.shell.alpm_transaction_get_targets()
      t = self.shell.alpm_transaction_get_sync_packages()

      self.fraction_increment = 1.0 / (2 + 2 * len(t))
      self.current_fraction = self.current_fraction - ((len(t) - len(targets)) *
          self.fraction_increment)
      
      # Step 3: actually perform the removal
      self.alpm_run_in_thread_and_wait(self.shell.alpm_transaction_commit, {})
      if self.cancel_operation:
        self.shell.alpm_transaction_release()
        self.busy_dialog.hide()
        return
      if self.shell.last_exception:
        if self.shell.last_exception[0] == 3:
          inst = self.shell.last_exception[1]
          conflicts_error_dialog =\
            self.all_widgets.get_widget('conflicts_error_dialog')
          conflicts_error_label =\
            self.all_widgets.get_widget('conflicts_error_label')

          string = inst.args[0]

          conflicts_error_label.set_text(string)
          conflicts_error_dialog.run()
          conflicts_error_dialog.hide()
          
          self.shell.alpm_transaction_release()
          self.busy_dialog.hide()
          self.shell.last_exception = None
          return

      # for removed_pkg in list: {{{
      for removed_pkg in targets:
        # unset self.local_pkg_info and self.local_pkgs
        try:
          #del self.local_pkg_info[removed_pkg]
          del self.local_pkgs[removed_pkg]
        except KeyError:
          pass
      # refresh the local_groups
      # TODO: remove only the group(s) that were removed, don't refresh all of
      # them
      self.local_groups = self.shell.alpm_get_groups('local')
      # }}}

      self.shell.alpm_transaction_release()
      self.busy_dialog.hide()
      self.refresh_pkgs_treeview()
      return
  # }}}

  # def alpm_update_gui(self): {{{
  def alpm_update_gui(self):
    while gtk.events_pending():
      gtk.main_iteration(False)
    return True
  # }}}

  # def on_remove_pkg_clicked(self, button): {{{
  def on_remove_pkg_clicked(self, button):
    pkgs_to_remove = self.get_all_selected_packages(self.liststore, 1, 0)

    if pkgs_to_remove == []:
      return 

    self.alpm_remove_targets(pkgs_to_remove)
  # }}}

  # def on_install_from_repo_button_clicked(self, button): {{{
  def on_install_from_repo_button_clicked(self, button):
    # TODO: WARNING: To test this I have to use 'testing' repo :|
    repo_choice_dialog = self.all_widgets.get_widget('repo_choice_dialog')
    self.current_dialog = repo_choice_dialog
    repo_choice_combobox = self.all_widgets.get_widget('repo_choice_combobox')

    repo_liststore = gtk.ListStore(str)
    
    for repo in sorted(self.pkgs_by_repo.keys()):
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
      
      pkgs_to_install = self.get_all_selected_packages(self.liststore, 1, 0)

      if pkgs_to_install == []:
        return 
    
      self.alpm_install_targets(pkgs_to_install, repo_to_use)
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
    regexp_text = self.search_entry.get_text()
    if regexp_text == '':
      return

    self.search(regexp_text)
  # }}}

  # def on_search_changed(self, editable): {{{
  def on_search_changed(self, editable):
    regexp_text = editable.get_text()

    if regexp_text == '':
      self.__fill_treeview_with_pkgs_from_repo__('installed')
      return

    self.search(regexp_text)
  # }}}

  # def search(self, regexp_text): {{{
  def search(self, regexp_text):
    import cgi
    already_seen_pkgs = {}
    already_seen_groups = {} # grp name => iter

    self.treeview.set_model(None) # unsetting model to speed things up
    # selected, name, installed version, available version, repository
    self.liststore = gtk.TreeStore('gchararray', 'gboolean', 'gchararray',\
        'gchararray', 'gchararray', 'gchararray')

    # setup the treeview for 5 columns {{{
    #self.__setup_pkg_treeview_no_fill__()
    textrenderer = gtk.CellRendererText()
    togglerenderer = gtk.CellRendererToggle()
    togglerenderer.set_active(True)

    for col in self.treeview.get_columns():
      self.treeview.remove_column(col)

    #if self.treeview.get_columns() == []:
    emptycolumn = gtk.TreeViewColumn('')
    #emptycolumn.set_sort_column_id(0)
    emptycolumn.pack_start(togglerenderer)
    emptycolumn.set_attributes(togglerenderer, active=1)
    emptycolumn.set_clickable(True)
    emptycolumn.connect('clicked', self.on_treeview_column_clicked,\
        self.liststore, 1)
    
    repositorycolumn = gtk.TreeViewColumn('Repository')
    repositorycolumn.set_sort_column_id(5)
    repositorycolumn.pack_start(textrenderer)
    #repositorycolumn.set_attributes(textrenderer, text=5)
    repositorycolumn.set_attributes(textrenderer, markup=5)
    
    namecolumn = gtk.TreeViewColumn('Name', textrenderer, markup=2)
    namecolumn.set_resizable(True)
    namecolumn.set_min_width(300)
    namecolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
    namecolumn.set_sort_column_id(0)
    #namecolumn.pack_start(textrenderer)
    #namecolumn.set_attributes(textrenderer, text=1)
    
    availableversioncolumn = gtk.TreeViewColumn('Available')
    availableversioncolumn.set_sort_column_id(4)
    availableversioncolumn.pack_start(textrenderer)
    #availableversioncolumn.set_attributes(textrenderer, text=4)
    availableversioncolumn.set_attributes(textrenderer, markup=4)
    
    installedversioncolumn = gtk.TreeViewColumn('Installed')
    installedversioncolumn.set_sort_column_id(3)
    installedversioncolumn.pack_start(textrenderer)
    #installedversioncolumn.set_attributes(textrenderer, text=3)
    installedversioncolumn.set_attributes(textrenderer, markup=3)

    self.treeview.append_column(emptycolumn)
    self.treeview.append_column(namecolumn)
    self.treeview.append_column(installedversioncolumn)
    self.treeview.append_column(availableversioncolumn)
    self.treeview.append_column(repositorycolumn)
    # }}}

    if regexp_text[0] == '*':
      regexp_text = '.' + regexp_text
    if regexp_text[len(regexp_text) - 1] == '*':
      regexp_text += '.'
    try:
      regexp = re.compile(regexp_text)
    except sre_constants.error:
      pass
    search_combobox = self.all_widgets.get_widget('search_combobox')
    # TODO: use search_combobox.get_active() instead of get_active_text()?? 
    #       better for i18n? cleaner?
    # TODO: search in remote_pkg_info ??
    where_to_search = search_combobox.get_active_text()
    
    found = False
    if where_to_search != None:
      # search local groups
      if where_to_search == 'Name' or where_to_search == 'All':
        for grp_repo_name, repo_list in self.groups_by_repo.iteritems():
          for grp_name, grp_packages in repo_list:
            match = regexp.match(grp_name)
            if match:
              if grp_packages == []:
                break

              found = False
              try:
                iter, repo_name = already_seen_groups[grp_name]
              except KeyError:
                pass
              else:
                if repo_name == grp_repo_name:
                  found = True

              #if grp_name in already_seen_groups:
              if found:
                iter, repo_name = already_seen_groups[grp_name]
              else:
                grp_name = cgi.escape(grp_name)
                text = '<b>%s</b>\n<small><i>group</i></small>' % grp_name
                grp_repo_name = cgi.escape(grp_repo_name)
                text_grp_repo = '<b>%s</b>' % grp_repo_name
                iter = self.liststore.append(None, [grp_name, False, text, '',\
                    '', text_grp_repo])
                already_seen_groups[grp_name] = (iter, grp_repo_name)

              for pkg_name in grp_packages:
                already_seen_pkgs[pkg_name] = None
                pkg_repo, available_version, desc =\
                    self.alpm_get_highest_version_of_pkg(self.pkgs[pkg_name])

                try:
                  installed_version = self.local_pkgs[pkg_name][1]
                except KeyError:
                  installed_version = '--'

                # put it in the group
                #self.liststore.append(iter, [False, pkg_name, installed_version,\
                #    available_version, pkg_repo])
                pkg_name = cgi.escape(pkg_name)
                desc = cgi.escape(desc)
                #if len(desc) > 40:
                #  desc = desc[:40]
                #  desc += ' ...'
                text = '<b>%s</b>\n<small><i>%s</i></small>' % (pkg_name, desc)
                ver_markup = '<b>%s</b>'
                installed_version = cgi.escape(installed_version)
                available_version = cgi.escape(available_version)
                pkg_repo = cgi.escape(pkg_repo)
                text_local_ver = ver_markup % installed_version
                text_avai_ver = ver_markup % available_version
                text_pkg_repo = ver_markup % pkg_repo
                self.liststore.append(iter, [pkg_name, False, text,\
                    text_local_ver, text_avai_ver, text_pkg_repo])
                # and outside the group
                #self.liststore.append(None, [False, pkg_name, installed_version,\
                #    available_version, repo])

      # search current, community, extra, etc...
      for repo, repo_list in self.pkgs_by_repo.iteritems():
        for name, version, description in repo_list:
          matched = False
          if where_to_search == 'Version':
            match = regexp.match(version)
            matched = (match != None)
          elif where_to_search == 'Name':
            match = regexp.match(name)
            matched = (match != None)
          elif where_to_search == 'Description':
            match = regexp.match(description)
            matched = (match != None)
          elif where_to_search == 'All':
            matched = (regexp.match(version) != None\
              or regexp.match(name) != None\
              or regexp.match(description) != None)
          if matched:
            if name not in already_seen_pkgs:
              if (where_to_search == 'Name'\
                  or where_to_search == 'Description')\
                  or where_to_search == 'All' and not found:
                found = True
              try:
                installed_version = self.local_pkgs[name][1]
              except KeyError:
                installed_version = '--'
              description = cgi.escape(description)
              #if len(description) > 40:
              #  description = description[:40]
              #  description += ' ...'

              name = cgi.escape(name)
              description = cgi.escape(description)
              installed_version = cgi.escape(installed_version)
              version = cgi.escape(version)
              repo = cgi.escape(repo)
              ver_markup = '<b>%s</b>'
              text_local_ver = ver_markup % installed_version
              text_avai_ver = ver_markup % version
              text_pkg_repo = ver_markup % repo
              
              text = '<b>%s</b>\n<small><i>%s</i></small>' % (name, description)
              self.liststore.append(None, [name, False, text,\
                  text_local_ver, text_avai_ver, text_pkg_repo])
          
      if not found:
        # search 'local'
        for name in self.local_pkgs.keys():
          if name not in already_seen_pkgs:
            version = self.local_pkgs[name][1]
            description = self.local_pkgs[name][2]
            matched = False
            if where_to_search == 'Version':
              match = regexp.match(version)
              matched = match != None
            elif where_to_search == 'Name':
              match = regexp.match(name)
              matched = match != None
            elif where_to_search == 'Description':
              match = regexp.match(description)
              matched = match != None
            elif where_to_search == 'All':
              matched = regexp.match(version) != None\
                  or regexp.match(name) != None\
                  or regexp.match(description) != None
            if matched:
              if not found:
                found = True
              try:
                installed_version = self.local_pkgs[name][1]
              except KeyError:
                installed_version = '--'
              description = cgi.escape(description)
              #if len(description) > 40:
              #  description = description[:40]
              #  description += ' ...'

              name = cgi.escape(name)
              description = cgi.escape(description)
              installed_version = cgi.escape(installed_version)
              version = cgi.escape(version)
              repo = cgi.escape(repo)
              text_local_ver = ver_markup % installed_version
              text_avai_ver = ver_markup % available_version
              
              text = '<b>%s</b>\n<small><i>%s</i></small>' % (pkg_name, description)
              self.liststore.append(None, [pkg_name, False, text,\
                  text_local_ver, text_avai_ver, '<b>local</b>'])

      if self.toggle_handler_id:
        if not self.togglerenderer.handler_is_connected(self.toggle_handler_id):
          self.toggle_handler_id = togglerenderer.connect('toggled',\
            self.toggled, self.liststore, 1)
        else:
          self.togglerenderer.disconnect(self.toggle_handler_id)
          self.toggle_handler_id = togglerenderer.connect('toggled',\
            self.toggled, self.liststore, 1)
      else:
        self.toggle_handler_id = togglerenderer.connect('toggled',\
            self.toggled, self.liststore, 1)
      self.treeview.set_model(self.liststore)

    else: # this should not happen but it stays here for completeness
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

    name = treemodel.get_value(iter, 0)
    pkgs_to_install = [name]
    self.alpm_install_targets(pkgs_to_install)
  # }}}

  # def on_install_from_popup_menu_activate(self, menuitem): {{{
  def on_install_from_popup_menu_activate(self, menuitem):
    repo_choice_dialog = self.all_widgets.get_widget('repo_choice_dialog')
    self.current_dialog = repo_choice_dialog
    repo_choice_combobox = self.all_widgets.get_widget('repo_choice_combobox')

    repo_liststore = gtk.ListStore(str)
    
    for repo in sorted(self.pkgs_by_repo.keys()):
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

      name = treemodel.get_value(iter, 0)
      pkgs_to_install = [name]
      self.alpm_install_targets(pkgs_to_install, repo_to_use)
    else:
      return
  # }}}

  # def on_remove_popup_menu_activate(self): {{{
  def on_remove_popup_menu_activate(self, menuitem):
    selection = self.treeview.get_selection()
    treemodel, iter = selection.get_selected()
    if not iter:
      return 

    name = treemodel.get_value(iter, 0)
    pkgs_to_remove = [name]
    self.alpm_remove_targets(pkgs_to_remove)
  # }}}

  # def on_view_files_popup_menu_activate(self, menuitem): {{{
  def on_view_files_popup_menu_activate(self, menuitem):
    selection = self.treeview.get_selection()
    treemodel, iter = selection.get_selected()
    if not iter:
      return 

    name = treemodel.get_value(iter, 0)
    
    pkg_files_dialog = self.all_widgets.get_widget('pkg_files_dialog')

    pkg_files_textview = self.all_widgets.get_widget('pkg_files_textview')
    
    buffer = gtk.TextBuffer()
    pkg_files_textview.set_buffer(buffer)

    selection_repos = self.treeview_repos.get_selection()
    treemodel_repos, iter_repos = selection_repos.get_selected()

    if iter_repos:
      repo_name = treemodel_repos.get_value(iter_repos, 0).lower()
      lines = self.shell.alpm_get_package_files(name, repo_name)
    else:
      lines = self.shell.alpm_get_package_files(name)

    text = ''

    if lines:
      for line in lines:
        text = text + line + '\n'
    else:
      text = 'Viewing a package\'s files only works with installed packages.'

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
    tag_table = self.information_text.get_buffer().get_tag_table()
    hyperlink_tag = tag_table.lookup('hyperlink')

    if hyperlink_tag == None:
      print 'main_window None!!'
      return 
    
    hyperlink_tag.set_property('underline', self.pango_no_underline)
    self.information_text.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(None)
  # }}}
  
  # from pygtk-demo {{{
  # def set_cursor_if_appropriate(self, text_view, x, y): {{{
  # Looks at all tags covering the position (x, y) in the text view,
  # and if one of them is a link, change the cursor to the "hands" cursor
  # typically used by web browsers.
  def set_cursor_if_appropriate(self, text_view, x, y):
    hovering = False

    buffer = text_view.get_buffer()
    iter = text_view.get_iter_at_location(x, y)

    tags = iter.get_tags()
    for tag in tags:
      page = tag.get_data("page")
      if page != 0:
        hovering = True
        break

    if hovering != self.hovering_over_link:
      self.hovering_over_link = hovering

    if self.hovering_over_link:
      text_view.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(self.hand_cursor)
    else:
      text_view.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(self.regular_cursor)
  # }}}

  # def motion_notify_event(self, text_view, event): {{{
  # Update the cursor image if the pointer moved.
  def motion_notify_event(self, text_view, event):
    x, y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
        int(event.x), int(event.y))
    self.set_cursor_if_appropriate(text_view, x, y)
    text_view.window.get_pointer()
    return False
  # }}}

  # def visibility_notify_event(self, text_view, event): {{{
  # Also update the cursor image if the window becomes visible
  # (e.g. when a window covering it got iconified).
  def visibility_notify_event(self, text_view, event):
    wx, wy, mod = text_view.window.get_pointer()
    bx, by = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET, wx, wy)

    self.set_cursor_if_appropriate (text_view, bx, by)
    return False
  # }}}

  # def insert_link(self, buffer, iter, text): {{{
  def insert_link(self, buffer, iter, text):
    ''' Inserts a piece of text into the buffer, giving it the usual
        appearance of a hyperlink in a web browser: blue and underlined.
        Additionally, attaches some data on the tag, to make it recognizable
        as a link.
    '''
    tag = buffer.create_tag(None,
        foreground="blue", underline=pango.UNDERLINE_SINGLE)
    tag.set_data("url", text)
    buffer.insert_with_tags(iter, text, tag)
  # }}}

  # def event_after(self, text_view, event): {{{
  # Links can also be activated by clicking.
  def event_after(self, text_view, event):
    if event.type != gtk.gdk.BUTTON_RELEASE:
      return False
    if event.button != 1:
      return False
    buffer = text_view.get_buffer()

    # we shouldn't follow a link if the user has selected something
    try:
      start, end = buffer.get_selection_bounds()
    except ValueError:
      # If there is nothing selected, None is return
      pass
    else:
      if start.get_offset() != end.get_offset():
        return False

    x, y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
        int(event.x), int(event.y))
    iter = text_view.get_iter_at_location(x, y)

    tags = iter.get_tags()

    if len(tags) == 1:
      tag = tags[0]
      url = tag.get_data('url')
      if url:
        thread.start_new_thread(os.popen, (self.browser + ' ' + url, 'r'))
    return False
  # }}}
  # }}}

  # def on_cache_menu_activate(self, menuitem): {{{
  def on_cache_menu_activate(self, menuitem):
    # TODO: cache this to use in the 'Cleanup' button
    cache_dialog = self.all_widgets.get_widget('cache_dialog2')
    self.current_dialog = cache_dialog
    time_now = time.time()

    cache_treeview = self.all_widgets.get_widget('cache_treeview2')

    cache_liststore = gtk.TreeStore(str, str)
    
    textrenderer = gtk.CellRendererText()

    if cache_treeview.get_columns() == []:
      pkg_cache_name_column = gtk.TreeViewColumn('Name')
      pkg_cache_name_column.set_resizable(True)
      #pkg_cache_name_column.set_min_width(300)
      #pkg_cache_name_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
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
    
    self.alpm_run_in_thread_and_wait(self.get_cache_pkgs, {})
    cache_pkgs = self.prev_return

    self.already_seen = {}
    self.pkg_versions = {}
    to_clean = []
    to_clean_names = []
    
    cache_combobox = self.all_widgets.get_widget('cache_combobox')
    clean_by = cache_combobox.get_active_text()
    cache_spinbutton = self.all_widgets.get_widget('cache_spinbutton')
    clean_threshold = cache_spinbutton.get_value_as_int()

    cache_dir = self.shell.alpm.get_cache_dir()
    dir = os.path.join('/', cache_dir)

    for package in cache_pkgs:
      # strip '.pkg.tar.gz'
      try:
        index = package.index('.pkg.tar.gz')
      except ValueError:
        continue
      tmp = package[:index]
      pkg_name, pkg_version = self.split_pkg_name(tmp)
      
      try:
        iter_old = self.already_seen[pkg_name]
        self.pkg_versions[pkg_name]
        cache_liststore.append(iter_old, [pkg_name, pkg_version])
      except KeyError:
        iter = cache_liststore.append(None, [pkg_name, None])
        cache_liststore.append(iter, [pkg_name, pkg_version])
        self.already_seen[pkg_name] = iter

      appended = False
      try:
        self.pkg_versions[pkg_name].append(pkg_version)
        appended = True
      except KeyError:
        self.pkg_versions[pkg_name] = [pkg_version]

      if appended:
        # building the to_clean list {{{
        if not os.path.isdir(os.path.join(dir, pkg_name)):
          path = os.path.join(dir, package)

          if clean_by == 'Days':
            mtime = os.stat(path).st_mtime
            clean_secs = clean_threshold * 24 * 60 * 60
            if time_now - mtime >= clean_secs:
              length = len(self.pkg_versions[pkg_name])
              if length > 1:
                # more than one version
                if self.pkg_versions[pkg_name][length-1] != pkg_version:
                  del self.pkg_versions[pkg_name][0]
                  to_clean.append(path)
                  to_clean.append(pkg_name)
                else:
                  print 'trying to clean the last version: ',\
                    ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
              else:
                print 'there is only one version in cache: ',\
                  ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
          else:
            # cleanup by version
            length = len(self.pkg_versions[pkg_name])

            if length > clean_threshold:
              count = 0
              while count < clean_threshold:
                del self.pkg_versions[pkg_name][0]
                count += 1
              to_clean.append(path)
              to_clean.append(pkg_name)
        # }}}

    cache_treeview.set_model(cache_liststore)

    self.current_dialog_on = True
    response = cache_dialog.run()

    if response == gtk.RESPONSE_YES:
      # cleanup cache
      #self.alpm_run_in_thread_and_wait(self.cleanup_cache,\
      #    {'clean_by': clean_by, 'clean_threshold': clean_threshold\
      #     'to_clean': to_clean, 'to_clean_names': to_clean_names})
      self.cleanup_cache(clean_by, clean_threshold, to_clean, to_clean_names)
    else:
      pass
    cache_dialog.hide()
    self.current_dialog_on = False
  # }}}

  # def on_cancel_busy_button_clicked(self, button): {{{
  def on_busy_cancel_button_clicked(self, button):
    #if self.th:
    #  self.cancelled = True
    #  #print 'MAIN: acquiring lock...'
    #  self.lock.acquire()
    #
    #  #print 'MAIN: waiting for thread to finish'
    #  while self.th.isAlive():
    #    while gtk.events_pending():
    #      gtk.main_iteration(False)
    #    time.sleep(0.1)
    #  #print 'MAIN: thread finished, releasing lock'
    #  self.lock.release()
    self.busy_cancel_button.set_sensitive(False)
    self.cancel_operation = True
  # }}}
  # }}}
  
  # def alpm_get_pkgs_to_clean(self, clean_by, clean_threshold): {{{
  def alpm_get_pkgs_to_clean(self, clean_by, clean_threshold):
    cache_dir = self.shell.alpm.get_cache_dir()
    time_now = time.time()

    already_cleaned = {}
    to_clean = []

    dir = os.path.join('/', cache_dir)

    for package in sorted(os.listdir(dir)):
      try:
        index = package.index('.pkg.tar.gz')
      except ValueError:
        continue

      tmp = package[:index]
      pkg_name, pkg_version = self.split_pkg_name(tmp)

      if not os.path.isdir(os.path.join(cache_dir, package)):
        path = os.path.join(dir, package)

        if clean_by == 'Days':
          mtime = os.stat(path).st_mtime
          clean_secs = clean_threshold * 24 * 60 * 60
          if time_now - mtime >= clean_secs:
            length = len(self.pkg_versions[pkg_name])
            if length > 1:
              # more than one version
              if self.pkg_versions[pkg_name][length-1] != pkg_version:
                del self.pkg_versions[pkg_name][0]
                to_clean.append(path)
              else:
                print 'trying to clean the last version: ',\
                    ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
            else:
              print 'there is only one version in cache: ',\
                  ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
        else:
          # cleanup by version
          length = len(self.pkg_versions[pkg_name])

          if length > clean_threshold:
            count = 0
            while count < clean_threshold:
              del self.pkg_versions[pkg_name][0]
              count += 1
            to_clean.append(path)
    return to_clean
  # }}}

  # def cleanup_cache(self, clean_by, clean_threshold, to_clean, to_clean_names): {{{
  def cleanup_cache(self, clean_by, clean_threshold, to_clean, to_clean_names):
    # TODO: add an else branch that shows a dialog saying no packages were
    # removed
    if len(to_clean) > 0:
      generic_treeview_dialog =\
        self.all_widgets.get_widget('generic_treeview_dialog')
      generic_treeview_label =\
        self.all_widgets.get_widget('generic_treeview_label')
      generic_treeview_treeview =\
        self.all_widgets.get_widget('generic_treeview_treeview')

      lstore = gtk.TreeStore('gchararray')

      if generic_treeview_treeview.get_columns() == []:
        textrenderer = gtk.CellRendererText()

        namecolumn = gtk.TreeViewColumn('Name')
        namecolumn.set_resizable(True)
        namecolumn.set_min_width(300)
        namecolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        namecolumn.set_sort_column_id(0)
        namecolumn.set_attributes(textrenderer, text=0)

        generic_treeview_treeview.append_column(namecolumn)

      for pkg_name in to_clean_names:
        lstore.append([pkg_name])

      response = generic_treeview_dialog.run()
      generic_treeview_dialog.hide()

      if response == gtk.RESPONSE_OK:
        #self.busy_dialog = self.all_widgets.get_widget('busy_dialog')
        self.busy_dialog = self.all_widgets.get_widget('busy_dialog2')
        self.busy_cancel_button =\
        self.all_widgets.get_widget('busy_cancel_button')

        #self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar3')
        self.busy_progress_bar3 =\
        self.all_widgets.get_widget('busy_progress_bar4')
        self.busy_progress_bar3.set_fraction(0.0)
        #self.busy_status_label = self.all_widgets.get_widget('busy_status_label')
        self.busy_status_label = self.all_widgets.get_widget('busy_status_label2')
        self.busy_status_label.set_markup('<i>Please wait...</i>')

        # old {{{
        #cache_dir = self.shell.alpm.get_cache_dir()
        #time_now = time.time()
        #print 'now is: ', int(time_now)
        #
        #already_cleaned = {}
        #cleaned = []
        #dir = os.path.join('/', cache_dir)

        #for package in sorted(os.listdir(dir)):
        #  #print 'package: ', package
        #  try:
        #    index = package.index('.pkg.tar.gz')
        #  except ValueError:
        #    continue
        #  tmp = package[:index]
        #  pkg_name, pkg_version = self.split_pkg_name(tmp)

        #  if not os.path.isdir(os.path.join(cache_dir, package)):
        #    # do the cleanup
        #    path = os.path.join(dir, package)

        #    if clean_by == 'Days':
        #      # cleanup by days {{{
        #      mtime = os.stat(path).st_mtime
        #      clean_secs = clean_threshold * 24 * 60 * 60
        #      if time_now - mtime >= clean_secs:
        #        length = len(self.pkg_versions[pkg_name])
        #        if length > 1:
        #          # more than one version
        #          if self.pkg_versions[pkg_name][length-1] != pkg_version:
        #            # not trying to clean the last version
        #            #print 'removing: ', path
        #            del self.pkg_versions[pkg_name][0]
        #            cleaned.append(path)
        #            os.remove(path)
        #            #print 'cleaned: %s\n' % path
        #          else:
        #            print 'trying to clean the last version: ',\
        #              ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
        #        else:
        #          print 'there is only one version in cache: ',\
        #              ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
        #      # }}}
        #    else:
        #      # cleanup by version {{{
        #      length = len(self.pkg_versions[pkg_name])
        #      if length > clean_threshold:
        #        #print 'removing: ', path
        #        count = 0
        #        while count < clean_threshold:
        #          del self.pkg_versions[pkg_name][0]
        #          count = count + 1
        #        cleaned.append(path)
        #        os.remove(path)
        #        #print 'cleaned: %s\n' % path
        #      else:
        #        #print 'there are only ', length
        #        #print 'versions in cache: ',\
        #        #    ((pkg_name, pkg_version), self.pkg_versions[pkg_name])
        #        pass
        #      # }}}
        ##print 'pkgs cleaned: ', cleaned
        # }}}

        #to_clean = self.alpm_get_pkgs_to_clean(clean_by, clean_threshold)

        self.busy_dialog.show_now()
        print 'to_clean: ', to_clean
        l = len(to_clean)
        if l == 0:
          return
        count = 0
        fraction_increment = 1.0 / l
        fraction = 0.0
        for path in to_clean:
          time.sleep(0.5)
          count += 1
          fraction += fraction_increment
          self.busy_progress_bar3.set_fraction(fraction)
          self.busy_progress_bar3.set_text('%d out of %d files removed' % (count, l))
          self.busy_status_label.set_markup('<i>Removing %s ...</i>' % path)
          os.remove(path)
        self.busy_dialog.hide()

    else:
      nothing_to_clean_dialog =\
        self.all_widgets.get_widget('nothing_to_clean_dialog')
      nothing_to_clean_label =\
        self.all_widgets.get_widget('nothing_to_clean_label')

      nothing_to_clean_label.set_markup(\
        '<b>There were no packages in the cache to clean.</b>')
      nothing_to_clean_dialog.run()
      nothing_to_clean_dialog.hide()
    return
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
    return pkg_name2
  # }}}

  # def get_cache_pkgs(self): {{{
  def get_cache_pkgs(self):
    self.prev_return = None
    cache_dir = '/var/cache/pacman/pkg'

    ret = []
    
    for pkg_name in sorted(os.listdir(cache_dir)):
      if not os.path.isdir(os.path.join(cache_dir, pkg_name)):
        ret.append(pkg_name)
    self.prev_return = ret
    self.shell.th_ended_event.set()
    return
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
  
  # def download_packages_from_list(self, list): {{{
  def download_packages_from_list(self, list):
    downloaded_pkgs_dialog =\
        self.all_widgets.get_widget('downloaded_pkgs_dialog')
    self.current_dialog = downloaded_pkgs_dialog

    downloaded_pkgs_label =\
        self.all_widgets.get_widget('downloaded_pkgs_label')

    #self.busy_dialog = self.all_widgets.get_widget('busy_dialog')
    self.busy_dialog = self.all_widgets.get_widget('busy_dialog2')
    self.busy_cancel_button =\
    self.all_widgets.get_widget('busy_cancel_button')

    #self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar3')
    self.busy_progress_bar3 = self.all_widgets.get_widget('busy_progress_bar4')
    self.busy_progress_bar3.set_fraction(0.0)

    self.main_window.set_sensitive(False)

    self.busy_dialog.show_now()
    self.busy_window_on = True
    
    # TODO: see pacman-lib/src/pacman/sync.c:356
    kwargs = {'files': list, 'progress_bar': self.busy_progress_bar3,\
      'report_hook': self.alpm_urllib_report_hook}
    self.alpm_run_in_thread_and_wait(self.shell.alpm_download_packages, kwargs)
    if self.cancel_operation:
      self.shell.alpm_transaction_release()
      self.busy_dialog.hide()
      return
    filenames = self.shell.get_prev_return()
    print filenames

    self.busy_dialog.hide()
    self.main_window.set_sensitive(True)

    if not filenames:
      return None
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
    #try:
    #  pixbuf =\
    #    gtk.gdk.pixbuf_new_from_file(self.cwd + \
    #      '/share/guzuta/guzuta_icon_transparent.png')
    #except gobject.GError:
    #  try:
    #    pixbuf =\
    #        gtk.gdk.pixbuf_new_from_file(\
    #          '/usr/share/guzuta/guzuta_icon_transparent.png'\
    #        )
    #  except gobject.GError:
    #    print 'systray icon not found, bailing out'
    #    sys.exit(1)
    img.set_from_pixbuf(self.guzuta_icon)
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

  # def populate_local_pkg_list(self): {{{
  def populate_local_pkg_list(self):
    self.local_pkgs = self.shell.alpm_local_search()
  # }}}

  # def populate_pkgs_by_repo(self): {{{
  def populate_pkgs_by_repo(self):
    try:
      (self.pkgs_by_repo, self.pkgs, self.groups, self.groups_by_repo) =\
          self.shell.alpm_repofiles2()
    except RuntimeError, inst:
      print inst
      return
  # }}}

  # def populate_pkg_lists2(self): {{{
  def populate_pkg_lists2(self):
    self.db_names = self.shell.get_db_names()
    self.alpm_local_pkgs = self.shell.alpm_get_package_cache("local")
  # }}}

  # def populate_pkg_lists(self): {{{
  def populate_pkg_lists(self):
    self.populate_local_pkg_list()
    self.populate_pkgs_by_repo()
  # }}}

  # def __add_pkg_info_markuped_to_pkg_info_label__(self, lines, {{{
  # installed = True):
  def __add_pkg_info_markuped_to_pkg_info_label__(self, lines,
      installed = True):
    pkg_info_label = self.all_widgets.get_widget('pkg_info_label')
    label_text = ''
    if not installed:
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
          label_text = label_text + line.strip() + '\n'
    pkg_info_label.set_markup(label_text)
  # }}}

  # def __add_pkg_info_markuped_to_text_buffer__(self, text_buffer, {{{
  # lines, installed = True):
  def __add_pkg_info_markuped_to_text_buffer__(self, text_buffer, lines,
      installed = True):
    iterator = text_buffer.get_iter_at_offset(0)
    table = text_buffer.get_tag_table()

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

          text_buffer.insert_with_tags(iterator, bold_stuff, bold_tag)
        
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
            text_buffer.insert(iterator, ' ' + normal_stuff +\
                '\n')
          elif line.startswith('URL'):
            self.insert_link(text_buffer, iterator, normal_stuff)
            text_buffer.insert(iterator, '\n')
          else:
            text_buffer.insert(iterator, normal_stuff + '\n')
        else:
          text_buffer.insert(iterator, line + '\n')
  # }}}

  # def __refresh_pkgs_treeview__(self, iter_to_remove): {{{
  def __refresh_pkgs_treeview__(self, iter_to_remove):
    self.__setup_pkg_treeview__()
  # }}}

  # def __fill_treeview_with_pkgs_from_repo__(self, repo): {{{
  def __fill_treeview_with_pkgs_from_repo__(self, repo):
    # unselect the previous store
    store = self.treeview.get_model()

    for row in store:
      for child_row in row.iterchildren():
        store[child_row.path][0] = False
      store[row.path][0] = False
      
    self.column_selected = False
    self.treeview.set_model(None) # unsetting model to speed things up
    self.liststore = gtk.TreeStore('gchararray', 'gboolean', 'gchararray',\
        'gchararray', 'gchararray', 'gchararray')

    self.__setup_pkg_treeview_no_fill__(self.liststore)

    #if self.toggle_handler_id:
    #  if not self.togglerenderer.handler_is_connected(self.toggle_handler_id):
    #    self.toggle_handler_id = self.togglerenderer.connect('toggled',\
    #      self.toggled, self.liststore, 1)
    #  else:
    #    self.togglerenderer.disconnect(self.toggle_handler_id)
    #    self.toggle_handler_id = self.togglerenderer.connect('toggled',\
    #      self.toggled, self.liststore, 1)
    #else:
    #  self.toggle_handler_id = self.togglerenderer.connect('toggled',\
    #      self.toggled, self.liststore, 1)

    if repo == 'current' or repo == 'extra' or repo == 'community':
      # current, extra, community {{{
      groups = self.shell.alpm_get_groups(repo)

      tmp_dict = dict([(pkg_name,(repo, pkg_ver, desc))\
          for (pkg_name, pkg_ver, desc) in self.pkgs_by_repo[repo]])

      gobject.idle_add(self.alpm_fill_treestore_with_pkgs_and_grps(\
        self.treeview, self.liststore, tmp_dict, groups, repo).next)
      #self.alpm_fill_treestore_with_pkgs_and_grps(self.treeview,\
      #    self.liststore, tmp_dict, groups, repo)

      # }}}
    elif repo == 'groups':
      # groups {{{
      groups = {}

      for db_name in self.dbs_by_name:
        grp = self.shell.alpm_get_groups(db_name)
        groups.update(grp)

      gobject.idle_add(self.alpm_fill_treestore_with_pkgs_and_grps(\
        self.treeview, self.liststore, {}, groups).next)
      # }}}
    elif repo == 'installed':
      # installed {{{
      #self.local_groups = self.shell.alpm_get_groups('local')

      gobject.idle_add(self.alpm_fill_treestore_with_pkgs_and_grps(\
          self.treeview, self.liststore, self.local_pkgs, self.local_groups).next)
      #self.alpm_fill_treestore_with_pkgs_and_grps(self.treeview,\
      #    self.liststore, self.local_pkgs, self.local_groups)
      # }}}
    elif repo == 'all':
      # all {{{
      # community, extra, current

      groups = {}
      for db_name in self.dbs_by_name:
        groups.update(self.shell.alpm_get_groups(db_name))

      tmp_dict = {}
      for (repo, l) in self.pkgs_by_repo.iteritems():
        for (pkg_name, pkg_ver, desc) in l:
          tmp_dict[pkg_name] = (repo, pkg_ver, desc)

      gobject.idle_add(self.alpm_fill_treestore_with_pkgs_and_grps(\
          self.treeview, self.liststore, tmp_dict, groups).next)
      #self.alpm_fill_treestore_with_pkgs_and_grps(self.treeview,\
      #    self.liststore, tmp_dict, groups)

      # }}}
    elif repo == 'not installed':
      # not installed {{{

      # TODO: cache this
      # TODO: manually installed pkgs can be collected by
      #       checking if the packages in not_installed are from
      #       repo 'local'. cache this
      not_installed = xor_two_dicts(self.local_pkgs, self.pkgs)
      
      groups = {}

      for db_name in self.dbs_by_name:
        db_groups = self.shell.alpm_get_groups(db_name)
        for (grp_name, grp_pkgs) in db_groups.iteritems():
          if grp_name not in self.local_groups:
            # group not installed
            groups[grp_name] = grp_pkgs

      gobject.idle_add(self.alpm_fill_treestore_with_pkgs_and_grps(\
          self.treeview, self.liststore, not_installed, groups).next)
      #self.alpm_fill_treestore_with_pkgs_and_grps(self.treeview,\
      #    self.liststore, not_installed, groups)

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
    elif repo == 'pseudo repos':
      # pseudo repos {{{
      # do nothing
      pass
      # }}}
    else:
      # something else {{{
      groups = self.shell.alpm_get_groups(repo)

      tmp_dict = dict([(pkg_name,(repo, pkg_ver, desc))\
          for (pkg_name, pkg_ver, desc) in self.pkgs_by_repo[repo]])

      gobject.idle_add(self.alpm_fill_treestore_with_pkgs_and_grps(\
          self.treeview, self.liststore, tmp_dict, groups, repo).next)
      #self.alpm_fill_treestore_with_pkgs_and_grps(self.treeview,\
      #    self.liststore, tmp_dict, groups, repo)
      # }}}

    self.treeview.set_model(self.liststore)
  # }}}

  # def __is_root__(self): {{{
  def __is_root__(self):
    uid = posix.getuid()
    return uid == 0
  # }}}

  # def get_all_selected_packages(self, tree_model, boolean_col = 0, {{{
  #     name_col = 1):
  def get_all_selected_packages(self, tree_model, boolean_col = 0,\
      name_col = 1):
    n = len(tree_model)
    
    names = []
    for row in tree_model:
      has_children = False
      for child_row in row.iterchildren():
        has_children = True
        if child_row[boolean_col]:
          names.append(child_row[name_col])
      if (has_children == False) and (row[boolean_col]):
        names.append(row[name_col])

    return names
  # }}}

  # def refresh_pkgs_treeview(self): {{{
  def refresh_pkgs_treeview(self):
    selection = self.treeview_repos.get_selection()
    treemodel, iter = selection.get_selected()
    selection_pkgs = self.treeview.get_selection()
    treemodel_pkgs, iter_pkgs = selection_pkgs.get_selected()

    if not iter:
      self.__refresh_pkgs_treeview__(iter_pkgs)
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
          info = self.shell.alpm_info(installed_pkg)
        self.local_pkg_info[installed_pkg] = info

      if info == None:
        try:
          info = self.remote_pkg_info[installed_pkg]
          self.local_pkg_info[installed_pkg] = info
        except KeyError:
          info = self.shell.alpm_local_info(installed_pkg)
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
          
          description = info[i]
        else:
          pass
      self.local_pkgs[installed_pkg] = (repo, version, description)
  # }}}
# }}}

