"""
This is our master settings file.

Note: We are moving this out into our new BuildSettings logic for flexibility.
"""
import os
from warehouse.utils import BuildSettings
setpath = os.path.abspath(os.path.join(os.path.dirname(__file__)))
settings = BuildSettings('settings.ini', 'defaults.ini', setpath)
grids = BuildSettings('grids.ini', 'griddef.ini', setpath)
