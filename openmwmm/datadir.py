
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
import subprocess

DATA_README_FILES = ['readme']
DATA_DIR_VERSION = '1'

class InvalidModException( Exception ):
   pass

class NoDataDirException( Exception ):
   pass

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

   def _open_archive( self, archive_path ):
      
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

      if '' != data_prefix:
         return data_prefix
      else:
         return None

   def _install_file( self, archive, file_path, mod_id, mod_data_path ):

      # Handle no-datadir scenarios.
      if mod_data_path:
         install_path = os.path.join(
            self.path_data, file_path[len( mod_data_path ) + 1:]
         )
      else:
         install_path = os.path.join( self.path_data, file_path )

      try:
         os.makedirs( os.path.dirname( install_path ) )
      except:
         pass

      # TODO: Actually extract the file.
      try:
         with archive.open( file_path ) as file_file:
            with open( install_path, 'wb' ) as out_file:
               shutil.copyfileobj( file_file, out_file )
      except Exception, e:
         self.logger.error( 'Failed to install file "{}": {}'.format(
            install_path, e
         ) )
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

   def import_mod( self, mod_path, nodatadir=False ):
      
      # This is hacky, but try to recompress 7zip files in a format we can
      # read.
      mod_filename, mod_extension = os.path.splitext( mod_path )
      mod_filename = os.path.basename( mod_filename )
      if '.7z' == mod_extension:
         # Extract the archive somewhere temporary.
         temp_dir = tempfile.mkdtemp()
         temp_ex_path = os.path.join( temp_dir, mod_filename )
         extract_command = [
            '7z',
            'x',
            '-o{}'.format( temp_ex_path ),
            mod_path
         ]
         print extract_command
         subprocess.call( extract_command )

         # 7z archives often contain a "Data Files" directory.
         # TODO: Others can contain one, too! Go after them as well!
         for root, dir_names, file_names in os.walk( temp_ex_path ):
            for dir_name in dir_names:
               if 'Data Files' == dir_name:
                  os.rename(
                     os.path.join( root, dir_name ),
                     os.path.join( root, 'data' )
                  )

         mod_path = os.path.join( temp_dir, '{}.zip'.format( mod_filename ) )
         with zipfile.ZipFile( mod_path, 'w' ) as zip_file:
            for root, dir_names, file_names in os.walk( temp_ex_path ):
               for file_name in file_names:
                  zip_file.write( os.path.join( root, file_name ) )

         # TODO: Remove temporary directory.

      if not self.validate_mod( mod_path ):
         raise InvalidModException( 'Mod is not valid.' )

      # If we're supposed to have a data dir, then make sure we have one.
      if not nodatadir:
         with self._open_archive( mod_path ) as mod:
            if not self._find_data_archive( mod ):
               raise NoDataDirException( 'Mod is missing data dir.' )

      # Copy mod to data avail path.
      shutil.copy( mod_path, self.path_avail )

   def validate_mod( self, mod_path ):
      
      # Open mod archive and try to find data directory.
      try:
         mod = self._open_archive( mod_path )
         mod.close()
      except:
         return False
      # Sometimes mods are valid without a data directory.
      #if not self._find_data_archive( mod ):
      #   return False
      return True

   def list_available( self ):

      # TODO: Make sure valid hashed file for each mod is present.

      mods_out = []
      for entry in os.listdir( self.path_avail ):
         if self.validate_mod( os.path.join( self.path_avail, entry ) ):
            mods_out.append( entry )
      mods_out.sort()
      return mods_out

   def list_installed( self ):

      db_mods = self.database.execute(
         'SELECT mod_name FROM files_installed GROUP BY mod_name'
      )

      # Clean list on datadir side so it's not tuples.
      mods_out = []
      for mod in db_mods.fetchall():
         mods_out.append( mod[0] )

      mods_out.sort()
      return mods_out

   def install_mod( self, mod_filename, force=False ):

      mod_path = os.path.join( self.path_avail, mod_filename )

      if not self.validate_mod( mod_path ):
         raise InvalidModException( 'Mod is not valid.' )

      # Iterate through all files in the archive.
      archive = self._open_archive( mod_path )
      mod_data_path = self._find_data_archive( archive )
      if not mod_data_path:
         mod_data_path = ''
      files_install = []
      for file_path in self._list_archive( archive ):
         
         # Skip stuff outside data/.
         if not file_path.startswith( mod_data_path ):
            continue
            
         # Skip readme files.
         if os.path.basename( file_path ).lower() in DATA_README_FILES:
            continue

         # For each file in the archive, check if it exists in the database and
         # ask to remove existing copy if it does.
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

      # Perform the actual installation in the second pass.
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

