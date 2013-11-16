
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

class NoDataDirDialog( gtk.MessageDialog ):

   def __init__( self, *args, **kwargs ):

      # Set the initial properties.
      kwargs = {
         'flags': gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
         'type': gtk.MESSAGE_QUESTION,
         'buttons': gtk.BUTTONS_OK_CANCEL,
      }
      super( NoDataDirDialog, self ).__init__( *args, **kwargs )
      self.set_markup( 'Mod is missing data directory. Install anyway?' )

      #self.set_default_response( gtk.RESPONSE_OK )

   def run( self ):
      # Process the response.
      response = super( NoDataDirDialog, self ).run()
      self.destroy()
      if gtk.RESPONSE_OK == response:
         return True
      else:
         return False

