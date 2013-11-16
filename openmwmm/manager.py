
'''
This file is part of OpenMWMM.

OpenMWMM is free software: you can redistribute it and/or modify it under 
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

OpenMWMM is distributed in the hope that it will be useful, but WITHOUT ANY 
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more 
details.

You should have received a copy of the GNU General Public License along
with OpenMWMM.  If not, see <http://www.gnu.org/licenses/>.
'''

import gtk
import logging
import os
import openmwmm.datadir
import openmwmm.dialogs

class Manager( object ):

   window = None
   logger = None
   datadir = None
   mods_available = None
   mods_installed = None

   def __init__( self ):

      self.logger = logging.getLogger( 'openmwmm.manager' )

      # Create the main window.
      self.window = gtk.Window()
      self.window.set_title( 'OpenMW Mods' )
      self.window.connect( 'destroy', gtk.main_quit )

      mb = gtk.MenuBar()

      # Create a file menu.
      filemenu = gtk.Menu()
      filem = gtk.MenuItem( 'File' )
      filem.set_submenu( filemenu )

      importm = gtk.MenuItem( 'Import mod...' )
      importm.connect( 'activate', self.on_import )
      filemenu.append( importm )
      
      exitm = gtk.MenuItem( 'Exit' )
      exitm.connect( 'activate', gtk.main_quit )
      filemenu.append( exitm )

      mb.append( filem )

      # Create a mod menu.
      modmenu = gtk.Menu()
      modm = gtk.MenuItem( 'Mod' )
      modm.set_submenu( modmenu )

      installm = gtk.MenuItem( 'Install...' )
      installm.connect( 'activate', self.on_install )
      modmenu.append( installm )

      removem = gtk.MenuItem( 'Remove...' )
      removem.connect( 'activate', self.on_remove )
      modmenu.append( removem )

      mb.append( modm )

      # Create the available mods list.
      self.mods_available = gtk.List()
      self.mods_available.connect( 'selection_changed', self.on_mod_selection )
      mods_available_scroller = gtk.ScrolledWindow()
      mods_available_scroller.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
      mods_available_scroller.add_with_viewport( self.mods_available )

      # Create the installed mods list.
      self.mods_installed = gtk.List()
      mods_installed_scroller = gtk.ScrolledWindow()
      mods_installed_scroller.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
      mods_installed_scroller.add_with_viewport( self.mods_installed )

      hbox = gtk.HBox( False, 2 )
      hbox.pack_start( mods_available_scroller, True, True, 0 )
      hbox.pack_start( mods_installed_scroller, True, True, 0 )

      # TODO: Allow loading data dir from menu or config.
      self.datadir = openmwmm.datadir.DataDir(
         os.path.join( os.path.expanduser( '~' ), '.config', 'openmw' )
      )
      self.show_mods()

      vbox = gtk.VBox( False, 2 )
      vbox.pack_start( mb, False, False, 0 )
      vbox.pack_start( hbox, True, True, 0 )
      self.window.add( vbox )
      self.window.show_all()

      gtk.main()

   def show_mods( self ):

      # Clear the list boxes.
      for child in self.mods_available.get_children():
         child.destroy()
      for child in self.mods_installed.get_children():
         child.destroy()

      for mod in self.datadir.list_available():
         # Create and add the listbox item.
         label = gtk.Label( mod )
         label.set_alignment( 0, 0.5 )
         label.show()
         list_item = gtk.ListItem()
         list_item.add( label )
         list_item.set_data( 'mod', mod )
         list_item.show()
         self.mods_available.add( list_item )

      for mod in self.datadir.list_installed():
         # Create and add the listbox item.
         # TODO: Clean list on datadir side so it's not tuples.
         label = gtk.Label( mod[0] )
         label.set_alignment( 0, 0.5 )
         label.show()
         list_item = gtk.ListItem()
         list_item.add( label )
         list_item.set_data( 'mod', mod[0] )
         list_item.show()
         self.mods_installed.add( list_item )

   def on_import( self, widget ):

      # TODO: Display import dialog.

      # Display a file open dialog.
      dialog =  gtk.FileChooserDialog(
         'Import mod...',
         None,
         gtk.FILE_CHOOSER_ACTION_OPEN,
         (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OPEN, gtk.RESPONSE_OK)
      )
      dialog.set_default_response( gtk.RESPONSE_OK )

      modfilter = gtk.FileFilter()
      modfilter.set_name( 'Morrowind Mod' )
      modfilter.add_pattern( '*.zip' )
      modfilter.add_pattern( '*.rar' )
      modfilter.add_pattern( '*.7z' )
      dialog.add_filter( modfilter )

      # Perform the actual import.
      try:
         response = dialog.run()
         if gtk.RESPONSE_OK == response:
            self.datadir.import_mod( dialog.get_filename() )
            self.show_mods()
      except openmwmm.datadir.NoDataDirException, e:
         self.logger.warn( 'Mod missing data dir: {}'.format(
            dialog.get_filename()
         ) )
         if openmwmm.dialogs.NoDataDirDialog( self.window ).run():
            self.datadir.import_mod( dialog.get_filename(), True )
      except openmwmm.datadir.InvalidModException, e:
         self.logger.error( 'Unable to import mod: {}'.format( e.message ) )
      finally:     
         dialog.destroy()

      # Refresh.
      self.show_mods()

   def on_install( self, widget ):

      for item in self.mods_available.get_selection():
         mod = item.get_data( 'mod' )
         self.logger.debug( 'Install selected mod: {}'.format( mod ) )
         # TODO: Error dialog on failure.
         self.datadir.install_mod( mod )

      # Refresh.
      self.show_mods()

   def on_remove( self, widget ):

      for item in self.mods_installed.get_selection():
         mod = item.get_data( 'mod' )
         self.logger.debug( 'Remove selected mod: {}'.format( mod ) )
         self.datadir.remove_mod( mod )

      # Refresh.
      self.show_mods()

   def on_mod_selection( self, widget ):
      selection = widget.get_selection()
      
      if not selection:
         return

      # Load the selection text into the editor.
      for item in selection:
         contents = item.get_data( 'mod' )

         # TODO: Show the mod readme in a viewer pane.

