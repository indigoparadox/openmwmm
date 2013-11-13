#!/usr/bin/env python

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

import sys
from distutils.core import setup

# TODO: Make an XDG desktop definition.

setup(
   name='openmwmm',
   # TODO: Figure out a way to grab the repo revision or something.
   version='0.1',
   packages=['openmwmm'],
   scripts=['omwmm.py'],
)

