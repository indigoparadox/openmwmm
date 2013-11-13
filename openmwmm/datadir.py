
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

import logging
import os
import shutil
import sqlite3
import zipfile
import rarfile
import re
import tempfile

DATA_README_FILES = ['readme']
DATA_DIR_VERSION = '1'

class DataDir( object ):

   logger = None
   path = None
   path_data = ''
   path_avail = ''
   database = None

   def __init__( self, data_path ):

      self.logger = logging.getLogger( 'openmwmm.datadir' )

      self.path = data_path

      # TODO: Get data/avail paths from configuration.
      self.path_data = os.path.join( self.path, 'data' )
      self.path_avail = os.path.join( self.path, 'mods' )

      # Create ~/.config/openmw/data_avail for available mods.
      if not os.path.isdir( self.path_data ):
         os.mkdir( self.path_data )
      if not os.path.isdir( self.path_avail ):
         os.mkdir( self.path_avail )

      self.database = sqlite3.connect( os.path.join( self.path, 'omwmm.db' ) )
      try:
         db_version = self.database.execute(
            "SELECT value FROM system WHERE key = 'version'"
         )
      except sqlite3.OperationalError, e:
         # No system table or version row, so create the database.
         self._setup_database()

   def _setup_database( self ):
      self.database.execute( 'CREATE TABLE system (key text, value text)' )
      self.database.execute(
         'CREATE TABLE files_installed (' + \
            'mod_name text collate nocase, ' + \
            'file_path text collate nocase, ' + \
            'ins_date text' + \
         ')'
      )
      self.database.execute(
         'CREATE INDEX file_path_index ON files_installed ' + \
            '(file_path collate nocase)'
      )
      self.database.execute(
         'INSERT INTO system VALUES (?, ?)', ('version', DATA_DIR_VERSION)
      )
      self.database.commit()

      # TODO: Set current version in system table.

   def _open_archive( self, archive_path ):
      
      # TODO: Support ZIP, RAR, 7-ZIP.

      try:
         return zipfile.ZipFile( archive_path )
      except:
         pass
      try:
         return rarfile.RarFile( archive_path )
      except Exception, e:
         self.logger.error(
            'Unable to open archive: {}'.format( archive_path )
         )
         self.logger.error( e.message )

   def _list_archive( self, archive_file ):
      list_out = []
      for item in archive_file.namelist():
         list_out.append( item.replace( '\\', '/' ) )
      return list_out

   def _find_data_archive( self, archive_file ):

      data_prefix = ''
      data_re = re.compile( r'^.*(/)?[Dd][Aa][Tt][Aa]' )
      for path in self._list_archive( archive_file ):

         # Try breaking stuff off until we find data/.
         path_split = os.path.split( path )
         while not path_split[0].lower().endswith( 'data' ):
            path_split = os.path.split( path_split[0] )
            if '' == path_split[0]:
               break

         # Make sure the name isn't something like foo_data.
         if data_re.search( path_split[0] ):
            data_prefix = path_split[0]

      return data_prefix

   def _install_file( self, archive, file_path, mod_id, mod_data_path ):

      install_path = os.path.join(
         self.path_data, file_path[len( mod_data_path ) + 1:]
      )

      try:
         os.makedirs( os.path.dirname( install_path ) )
      except:
         pass

      # TODO: Actually extract the file.
      try:
         with archive.open( file_path ) as file_file:
            with open( install_path, 'wb' ) as out_file:
               shutil.copyfileobj( file_file, out_file )
      except:
         self.logger.error(
            'Failed to install file: {}'.format( install_path )
         )
         return

      # Log the installation of this file in the database.
      self.database.execute(
         'INSERT INTO files_installed VALUES (?, ?, ?)',
         (mod_id, install_path, 'NA')
      )

      self.logger.info( 'Installed file: {}'.format( install_path ) )

   def _remove_file( self, file_path ):
      
      try:
         os.unlink( file_path )
      except:
         self.logger.warn(
            'File missing, removing from inventory: {}'.format( file_path )
         )
      # Remove this file from the database.
      self.database.execute(
         'DELETE FROM files_installed WHERE file_path=?',
         (file_path,)
      )
      self.logger.info( 'Removed file: {}'.format( file_path ) )

   def import_mod( self, mod_path ):

      if not self.validate_mod( mod_path ):
         raise Exception( 'Mod is not valid.' )

      # Copy mod to data avail path.
      shutil.copy( mod_path, self.path_avail )

   def validate_mod( self, mod_path ):
      
      # TODO: Open mod archive and try to find data directory.

      return True

   def list_available( self ):

      # TODO: Make sure valid hashed file for each mod is present.

      mods_out = []
      for entry in os.listdir( self.path_avail ):
         if self.validate_mod( os.path.join( self.path_avail, entry ) ):
            mods_out.append( entry )
      return mods_out

   def list_installed( self ):

      db_mods = self.database.execute(
         'SELECT mod_name FROM files_installed GROUP BY mod_name'
      )
      #mods_out = []
      #while mod = db_mods.fetchone():
      #   mods_out.append( mod )
      # TODO: Clean list on datadir side so it's not tuples.
      return db_mods.fetchall()

   def install_mod( self, mod_filename, force=False ):

      mod_path = os.path.join( self.path_avail, mod_filename )

      if not self.validate_mod( mod_path ):
         raise Exception( 'Mod is not valid.' )

      # Iterate through all files in the archive.
      archive = self._open_archive( mod_path )
      mod_data_path = self._find_data_archive( archive )
      files_install = []
      for file_path in self._list_archive( archive ):
         
         # Skip stuff outside data/.
         if not file_path.startswith( mod_data_path ):
            continue
            
         # Skip readme files.
         if os.path.basename( file_path ).lower() in DATA_README_FILES:
            continue

         # TODO: For each file in the archive, check if it exists in the
         #       database and ask to remove existing copy if it does. For the
         #       database check, convert both filenames to caps to compare.

         install_path = os.path.join(
            self.path_data, file_path[len( mod_data_path ) + 1:]
         )
         db_file = self.database.execute(
            'SELECT file_path FROM files_installed WHERE file_path=?',
            (install_path,)
         )
         if db_file.fetchone():
            
            # TODO: Ask what to do.

            self.logger.warning(
               'File already present, not installing: {}'.format( install_path )
            )

            continue

         files_install.append( file_path )

      # TODO: Perform the actual installation in the second pass.
      for file_path in files_install:
         self._install_file( archive, file_path, mod_filename, mod_data_path )
      self.database.commit()

   def remove_mod( self, mod_filename ):

      db_mods = self.database.execute(
         'SELECT file_path FROM files_installed WHERE mod_name=?',
         (mod_filename,)
      )
      for file_path in db_mods.fetchall():
         self._remove_file( file_path[0] )
      self.database.commit()

