"""
This is our master settings file.

Note: We are moving this out into our new BuildSettings logic for flexibility.
"""
from warehouse.utils import BuildSettings
settings = BuildSettings('settings.ini', 'defaults.ini')
