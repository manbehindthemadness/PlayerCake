"""
Reads GPS data from serial
"""

import time
import board

import serial
from stage.settings import settings
import adafruit_gps
import RPi.GPIO as GPIO

RX = board.RX
TX = board.TX

# uart = busio.UART(TX, RX, baudrate=9600, timeout=30)  # This would be used on arduino
uart = serial.Serial(settings.gps_uart, timeout=10)
gps = adafruit_gps.GPS(uart)

gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')

gps.send_command(b'PMTK220,1000')

last_print = time.monotonic()
latitudes = []
longitudes = []


class ReadGPS:
    """
    Aptly named.
    """
    def __init__(self):

        self.gps = gps
        self.nx = None
        self.lat = None
        self.long = None
        self.latlong = [0, 0]

    def getpositiondata(self):
        """
        # For a list of all supported classes and fields refer to:
        # https://gpsd.gitlab.io/gpsd/gpsd_json.html

        """
        if GPIO.input(settings.gps_sync):  # Check if GPS data is ready
            self.gps.update()
            self.lat = gps.latitude
            self.long = gps.longitude
            if self.lat:
                self.latlong = [self.lat, self.long]
        return self
