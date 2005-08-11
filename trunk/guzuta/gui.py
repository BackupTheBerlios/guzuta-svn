#! /usr/bin/env python
# -*- coding: UTF-8 -*
# vim: set foldmethod=marker:

# TODO: find a way to install/remove a pkg and update the database and show the
# text in a popup window

# imports {{{
import pygtk
pygtk.require('2.0')
import gtk
if gtk.pygtk_version < (2,3,90):
  raise SystemExit
import gobject
import pango
import gtk.glade
import sys, os, posix
import re
#import gksu

from guzuta import *
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
  # def __setup_pkg_treeview__(self): {{{
  def __setup_pkg_treeview__(self):
    # checked, name, version, description 
    self.liststore = gtk.ListStore('gboolean', str, str, str)

    self.textrenderer = gtk.CellRendererText()
    self.togglerenderer = gtk.CellRendererToggle()
    self.togglerenderer.set_active(True)

    self.togglerenderer.connect('toggled', self.toggled)

    self.emptycolumn = gtk.TreeViewColumn('Status')
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
    self.liststore_repos = gtk.ListStore(str)

    self.textrenderer_repos = gtk.CellRendererText()
    self.textrenderer_repos.set_property('weight', 400)

    self.repocolumn = gtk.TreeViewColumn('Repositories')
    self.repocolumn.set_sort_column_id(1)
    self.repocolumn.pack_start(self.textrenderer_repos)
    self.repocolumn.set_attributes(self.textrenderer_repos, text=0)
    
    self.treeview_repos.append_column(self.repocolumn)
    
    self.liststore_repos.set_sort_column_id(0, gtk.SORT_ASCENDING)

    self.liststore_repos.append(['All'])
    self.liststore_repos.append(['Installed'])
    self.liststore_repos.append(['Not installed'])

    for repo,v in self.pkgs_by_repo.iteritems():
      repo = repo.capitalize()
      self.liststore_repos.append([repo])
    
    self.treeview_repos.set_model(self.liststore_repos)
  # }}}

  # def __init__(self, read_pipe = None, write_pipe = None): {{{
  def __init__(self, read_pipe = None, write_pipe = None):
    # signals !!!
    self.glade_file = 'guzuta2.glade'
    signals_dict = {\
#    'on_treeview_row_activated': self.row_activated,
    'on_treeview_cursor_changed': self.cursor_changed,
    'on_treeview_select_cursor_row': self.select_cursor_row,
    'on_treeview_repos_cursor_changed': self.cursor_changed,
    'on_treeview_repos_select_cursor_row': self.select_cursor_row,
    'on_mainwindow_delete_event': self.delete_event,
    'on_mainwindow_destroy': self.destroy,
    'on_update_db_popup_delete_event': self.on_update_db_popup_delete_event,
    'on_update_db_popup_destroy': self.destroy,
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
    'on_about_activate': self.on_about_activate
    }
    # end signals
    #self.pacman = pacman(self)
    self.treeview = None
    self.uid = posix.getuid()
    self.pkgs = {}
    self.local_pkg_info = {}
    self.remote_pkg_info = {}
    self.not_installed = {}

    self.shell = shell(command_line = None, interactive = True)
    self.populate_pkg_lists()
    # pid of pacman process
    self.pid = 0

    self.all_widgets = gtk.glade.XML(self.glade_file)
    self.textview = self.all_widgets.get_widget("textview")
    self.main_window = self.all_widgets.get_widget("mainwindow")
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

    #self.information_frame = gtk.Frame('ahaha')
    #self.vbox2.pack_end(self.information_frame)

    self.__setup_pkg_treeview__()
    self.__setup_repo_treeview__()

    self.main_window.show_all()

    self.all_widgets.signal_autoconnect(signals_dict)

    #print self.remote_pkg_info

    gtk.main()
  # }}}

  # def populate_remote_pkg_info(self): {{{
  def populate_remote_pkg_info(self):
    for repo,v in self.pkgs_by_repo.iteritems():
      for pkg_desc in v:
        name = pkg_desc[0]
        self.remote_pkg_info[name] = self.shell.info(name)
  # }}}

  # def on_about_activate(self): {{{
  def on_about_activate(self, menuitem):
    about_dialog = self.all_widgets.get_widget('about_dialog')

    about_dialog.run()
    about_dialog.hide()
  # }}}

  # def populate_local_pkg_list(self): {{{
  def populate_local_pkg_list(self):
    self.local_pkgs = self.shell.local_search()
  # }}}
  
  # def populate_pkgs_by_repo(self): {{{
  def populate_pkgs_by_repo(self):
    #(self.pkgs_by_repo, self.pkgs) = self.shell.repofiles()
    (self.pkgs_by_repo, self.pkgs) = self.shell.repofiles2()
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
  
  # def row_activated(self, treeview, path, column): {{{
  #def row_activated(self, treeview, path, column):
  #  print 'row!'
  #  print 'treeview :',treeview
  #  print 'path :',path
  #  print 'column :',column
  # }}}

  # def __add_pkg_info_markuped_to_text_buffer__(self, text_buffer, {{{
  # lines, installed = True):
  def __add_pkg_info_markuped_to_text_buffer__(self, text_buffer, lines,
      installed = True):
    iterator = text_buffer.get_iter_at_offset(0)
    table = text_buffer.get_tag_table()
    tag = table.lookup('bold')
    if tag == None:
      tag = text_buffer.create_tag('bold', weight=pango.WEIGHT_BOLD)
    
    if not installed:
      text_buffer.insert_with_tags_by_name(iterator,
          'Package not installed!\n\n', 'bold')
      
    pattern = ':'

    # add text accordingly, 'bolding' the 'Name    :', etc
    for line in lines:
      if line != '':
        match_object = re.search(pattern, line)
        
        if match_object != None:
          text_buffer.insert_with_tags_by_name(iterator,
              line[:match_object.start()+1], 'bold')
          text_buffer.insert(iterator, line[match_object.start()+1:] + '\n')
        else:
          text_buffer.insert(iterator, line + '\n')
  # }}}

  # def cursor_changed(self, treeview): {{{
  def cursor_changed(self, treeview):
    selection = treeview.get_selection()
    treemodel, iter = selection.get_selected()
    info = ''
    if not iter:
      return

    if treeview == self.treeview:
      # treeview of pkgs
      name = treemodel.get_value(iter, 1)
      
      try:
        info = self.local_pkg_info[name]
      except KeyError:
        info = self.shell.local_info(name)
        self.local_pkg_info[name] = info
      
      buffer = gtk.TextBuffer()
      self.information_text.set_buffer(buffer)

      if info == None:
        try:
          remote_info = self.remote_pkg_info[name]
        except KeyError:
          remote_info = self.shell.info(name)
          self.remote_pkg_info[name] = remote_info
        
        self.__add_pkg_info_markuped_to_text_buffer__(buffer, remote_info,
            installed = False)
      else:
        self.__add_pkg_info_markuped_to_text_buffer__(buffer, info)

    else: # treeview of repos
      repo = treemodel.get_value(iter, 0)
      # fill treeview with pkgs from 'repo'
      self.__fill_treeview_with_pkgs_from_repo__(repo.lower())
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
      
      buffer = gtk.TextBuffer()
      self.information_text.set_buffer(buffer)
      
      new_liststore.append([False, name, installed_version, available_version])
    self.liststore = new_liststore
    self.treeview.set_model(self.liststore)
    #self.treeview.emit('cursor_changed')
  # }}}

  # def __fill_treeview_with_pkgs_from_repo__(self, repo): {{{
  def __fill_treeview_with_pkgs_from_repo__(self, repo):
    self.liststore = gtk.ListStore('gboolean', str, str, str)

    self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

    if repo != 'all' and repo != 'installed' and repo != 'not installed':
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
      self.treeview.set_model(self.liststore)
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
      self.treeview.set_model(self.liststore)
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
      self.treeview.set_model(self.liststore)
      # }}}
    else:
      # not installed {{{
      not_installed = xor_two_dicts(self.local_pkgs, self.pkgs)
      # pkg: repo, version
      for name, v in not_installed.iteritems():
        self.liststore.append([False, name, '--', v[1]])
      self.treeview.set_model(self.liststore)
      # }}}
  # }}}

  # def select_cursor_row(self, treeview, start_editing): {{{
  def select_cursor_row(self, treeview, start_editing):
    #print 'select_cursor_row'
    print treeview
    print start_editing
    print treeview.get_cursor()
  # }}}

  # def on_quit_activate(self, menuitem): {{{
  def on_quit_activate(self, menuitem):
    gtk.main_quit()
  # }}}

  # def destroy(self, widget, data=None): {{{
  def destroy(self, widget, data=None):
    if widget == self.main_window:
      gtk.main_quit()
    else:
      self.update_db_popup.hide()
      return False
  # }}}

  # def on_install_pkg_popup_destroy(self, widget, data=None): {{{
  def on_install_pkg_popup_destroy(self, widget, data=None):
    self.install_pkg_popup.hide()
    return False
  # }}}

  # def delete_event(self, widget, event, data=None): {{{
  def delete_event(self, widget, event, data=None):
    return False
  # }}}
  
  # def on_install_pkg_popup_delete_event(self, widget, event, data=None): {{{
  def on_install_pkg_popup_delete_event(self, widget, event, data=None):
    return False
  # }}}

  # def __is_root__(self): {{{
  def __is_root__(self):
    uid = posix.getuid()
    return uid == 0
  # }}}

  # def on_update_db_clicked(self, button): {{{
  def on_update_db_clicked(self, button):
    if button == self.update_db and self.__is_root__():
      ret, ret_err = self.shell.updatedb()
      #print ret, ret_err
      #self.shell.get_read_pipe()
      self.update_db_popup = self.all_widgets.get_widget('update_db_popup')
      #self.update_db_popup.show()
      response = self.update_db_popup.run()

      self.update_db_popup.hide()

      updates, updates_text = self.shell.get_fresh_updates()
      #print updates

      fresh_updates_dialog = self.all_widgets.get_widget('fresh_updates_dialog')
      fresh_updates_label = self.all_widgets.get_widget('fresh_updates_label')

      fresh_updates_label.set_text(updates_text)

      response = fresh_updates_dialog.run()
      fresh_updates_dialog.hide()
      
      fresh_updates_installed = False
      
      if response == gtk.RESPONSE_OK:
        self.shell.install_fresh_updates()
        fresh_updates_installed = True  

      #for (pkg_name, pkg_version) in updates:
      # TODO: is this necessary?
      for pkg_name in updates:
        info = self.shell.info(pkg_name)
        #print 'info: ', info
        #self.local_pkg_info[pkg_name] = info
        #print self.local_pkg_info[pkg_name]
        self.remote_pkg_info[pkg_name] = info
        #print self.local_pkgs
      if fresh_updates_installed:
        self.__add_pkg_info_to_local_pkgs__(updates)

      return
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

  # def install_packages(self, pkg_list): {{{
  def install_packages(self, pkg_list):
    what = ''
    pkg_names_by_comma = ''

    for pkg_name in pkg_list:
      what = what + pkg_name + ' '
      if pkg_names_by_comma == '':
        # first
        pkg_names_by_comma = pkg_name
      else:
        pkg_names_by_comma = pkg_names_by_comma + ', ' + pkg_name
    
    (ret, output) = self.shell.install_part_1(what)

    if ret:
      # is/are already up to date, get confirmation from user about forcing the
      # install of the package
      
      install_pkg_error = self.all_widgets.get_widget('install_pkg_error')
      install_pkg_error_label =\
      self.all_widgets.get_widget('install_pkg_error_label')
      #install_pkg_error_label.set_use_markup(True)
      text = '''<span weight="bold">Package(s) %s is(are) up to date.</span>
<span weight="bold">Upgrade anyway?</span>''' % pkg_names_by_comma
      install_pkg_error_label.set_markup(text)
      response2 = install_pkg_error.run()

      install_pkg_error.hide()
      if response2 == gtk.RESPONSE_CANCEL:
        return (False, output)
      elif response2 == gtk.RESPONSE_OK:
        return (True, output)
    else:
      return (None, output)
    #return ret

    #retcode_dict = {}
    #for pkg_name in pkg_list:
    #  ret = self.shell.install(pkg_name)
    #  if self.yesno:
    #    #self.shell.send_to_pacman
    #    pass
    #  retcode_dict[pkg_name] = ret

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
          info = self.shell.info(installed_pkg)
        self.local_pkg_info[installed_pkg] = info

      if info == None:
        info = self.remote_pkg_info[installed_pkg]
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

  # def on_install_pkg_clicked(self, button): {{{
  def on_install_pkg_clicked(self, button):
    self.install_pkg_popup = self.all_widgets.get_widget('install_pkg_popup')
    pkgs_to_install = self.get_all_selected_packages(self.liststore)

    if pkgs_to_install == []:
      return
    
    (retcode, output) = self.install_packages(pkgs_to_install)

    # TODO: do the same for remove pkg, add 'Are you sure?' dialog to remove
    if retcode == False:
      # cancel
      (exit_status, out) = self.shell.install_part_3('n')
      # TODO: check for proper pkg removal
      #self.shell.sigkill()
      print 'retcode was False, bailing now with exit_status: ',\
        exit_status, out
      return
    elif retcode == True:
      # force upgrade 
      #self.shell.sigkill()
      #exit_status = self.shell.install_packages_noconfirm(pkgs_to_install)
      out = self.shell.install_part_2('Y')
      (exit_status, out) = self.shell.install_part_3('Y')
      self.__add_pkg_info_to_local_pkgs__(pkgs_to_install)
      self.refresh_pkgs_treeview()
      # TODO: check for proper pkg install, check for file conflicts, etc. Build
      # another popup
      print 'retcode was True, bailing now with exit_status: ', exit_status
      return
    else:
      # display generic_cancel_ok, all went well, prompt user for action
      generic_cancel_ok = self.all_widgets.get_widget('generic_cancel_ok')

      generic_cancel_ok_label =\
      self.all_widgets.get_widget('generic_cancel_ok_label')

      text = '''<span weight="bold">Warning</span>
%s''' % output[:-7]

      generic_cancel_ok_label.set_markup(text)
      response3 = generic_cancel_ok.run()

      generic_cancel_ok.hide()
      
      if response3 == gtk.RESPONSE_OK: 
        self.shell.install_part_2('Y')
        response = self.install_pkg_popup.run()
        self.__add_pkg_info_to_local_pkgs__(pkgs_to_install)
        self.refresh_pkgs_treeview()
      elif response3 == gtk.RESPONSE_CANCEL:
        self.shell.install_part_2('n')

      self.install_pkg_popup.hide()

      #try:
      #  print self.local_pkg_info['abcm2ps']
      #except KeyError:
      #  print 'not found in local'
      #try:
      #  print self.remote_pkg_info['abcm2ps']
      #except KeyError:
      #  print 'not found in remote'

    #self.install_pkg_popup.hide()
  # }}}

  # def remove_packages(self, pkg_list): {{{
  def remove_packages(self, pkg_list):
    what = ''

    for pkg_name in pkg_list:
      what = what + pkg_name + ' '
    
    #self.remove_noconfirm(what)
    (exit_status, dependencies, out) = self.shell.remove(what)
    return (exit_status, dependencies, out)
  # }}}
  
  # def on_remove_pkg_clicked(self, button): {{{
  def on_remove_pkg_clicked(self, button):
    self.remove_pkg_popup = self.all_widgets.get_widget('remove_pkg_popup')
    pkgs_to_remove = self.get_all_selected_packages(self.liststore)

    if pkgs_to_remove == []:
      return

    remove_pkg_are_you_sure =\
    self.all_widgets.get_widget('remove_pkg_are_you_sure')

    are_you_sure_label = self.all_widgets.get_widget('are_you_sure_label')

    #text = 'Are you sure you want to remove the following packages?\n'
    text = ''

    for pkg_name in pkgs_to_remove:
      text = text + pkg_name + '\n'

    are_you_sure_label.set_text(text)
    response = remove_pkg_are_you_sure.run()
    remove_pkg_are_you_sure.hide()

    if response == gtk.RESPONSE_CANCEL:
      return
    else:
      (exit_status, dependencies, out) =\
      self.remove_packages(pkgs_to_remove)

      if exit_status != 0:
        # error ocurred
        self.remove_pkg_error = self.all_widgets.get_widget('remove_pkg_error')
        self.remove_dependencies_broken =\
        self.all_widgets.get_widget('remove_dependencies_broken')
       
        #for dep in dependencies:
        self.remove_dependencies_broken.set_text(out.rstrip())
        response = self.remove_pkg_error.run()
        self.remove_pkg_error.hide()
      else:
        response = self.remove_pkg_popup.run()

        if response == gtk.RESPONSE_OK:
          # force
          pass
        self.remove_pkg_popup.hide()

        # for removed_pkg in pkgs_to_remove: {{{
        for removed_pkg in pkgs_to_remove:
          # unset self.local_pkg_info and self.local_pkgs
          try:
            del self.local_pkg_info[removed_pkg]
            del self.local_pkgs[removed_pkg]
          except KeyError:
            pass
        # }}}

        self.refresh_pkgs_treeview()

    #try:
    #  print self.local_pkg_info['abcm2ps']
    #except KeyError:
    #  print 'not found in local'
    #try:
    #  print self.remote_pkg_info['abcm2ps']
    #except KeyError:
    #  print 'not found in remote'
  # }}}
  
  # def on_update_db_popup_delete_event(self, widget, event, data=None): {{{
  def on_update_db_popup_delete_event(self, widget, event, data=None):
    self.update_db_popup.hide()
    self.update_db_popup.destroy()
    return True
  # }}}

  # def on_search_clicked(self): {{{
  def on_search_clicked(self, button):
    self.liststore = gtk.ListStore('gboolean', str, str, str)

    self.liststore.set_sort_column_id(1, gtk.SORT_ASCENDING)

    regexp = re.compile(self.search_entry.get_text())
    search_combobox = self.all_widgets.get_widget('search_combobox')
    # search current, extra, community
    # self.pkgs_by_repo: dict of repos with lists of pairs with
    # (name, version)
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
          
      self.treeview.set_model(self.liststore)
  # }}}

  # def on_clear_clicked(self): {{{
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
# }}}

