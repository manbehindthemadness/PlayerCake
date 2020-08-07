"""
Reads GPS data from serial
"""

from gps import gps, watch_options


class ReadGPS:
    """
    Aptly named.
    """
    def __init__(self):

        self.gpsd = gps(mode=watch_options.WATCH_ENABLE | watch_options.WATCH_NEWSTYLE)
        self.nx = None
        self.lat = None
        self.long = None
        self.latlong = [0, 0]

    def getpositiondata(self):
        """
        # For a list of all supported classes and fields refer to:
        # https://gpsd.gitlab.io/gpsd/gpsd_json.html

        """
        self.nx = self.gpsd.next()

        if self.nx['class'] == 'TPV':
            self.lat = getattr(self.nx, 'lat', "Unknown")
            self.long = getattr(self.nx, 'lon', "Unknown")
            self.latlong = [self.lat, self.long]
        # else:
            # print('error', self.nx)

        return self
