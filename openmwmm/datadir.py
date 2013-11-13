
'''
This file is part of OpenMWMM.

OpenMWMM is free software: you can redistribute it and/or modify it under 
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

OpenMWMM is distributed in the hope that it will be useful, but WITHOUT ANY 
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more 
details.

You should have received a copy of the GNU Lesser General Public License along
with OpenMWMM.  If not, see <http://www.gnu.org/licenses/>.
'''

import logging
import os
import shutil
import sqlite3

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
         '''CREATE TABLE files_installed
         (mod_hash text, file_path text, ins_date text)'''
      )

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

   def remove_file( self, mod_id, path_rel_data ):
      
      # TODO: Remove this file from the database.

      pass

   def install_file( self, mod_id, path_rel_data, path_rel_arc, arcz ):
      
      # TODO: Log the installation of this file in the database.

      pass

   def install_mod( self, mod_path, force=False ):
      
      # TODO: For each file in the archive, check if it exists in the database
      #       and ask to remove existing copy if it does.

      # TODO: Perform the actual installation in the second pass.

      pass

