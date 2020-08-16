"""
This is a series of I/O classes that perform much faster then the bundled RPi.GPIO stuff.
"""
import time
import board
# import busio
import serial
from warehouse.utils import Fade
from stage import settings
import adafruit_gps

RX = board.RX
TX = board.TX

# uart = busio.UART(TX, RX, baudrate=9600, timeout=30)
uart = serial.Serial(settings.GPS_UART, timeout=10)
gps = adafruit_gps.GPS(uart)

gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')

gps.send_command(b'PMTK220,1000')

last_print = time.monotonic()
latitudes = []
longitudes = []
while True:
    gps.update()

    current = time.monotonic()
    if current - last_print >= 1.0:
        latitude = Fade(settings.GPS_Fade, latitudes, gps.latitude)  # Filter lat.
        latitudes = latitude[1]
        longitude = Fade(settings.GPS_Fade, longitudes, gps.longitude)  # Filter long.
        longitudes = longitude[1]
        last_print = current
        if not gps.has_fix:
            print('Waiting for fix...')
            continue
        print('=' * 40)  # Print a separator line.
        print('Latitude: {0:.6f} degrees'.format(latitude[0]))
        print('Longitude: {0:.6f} degrees'.format(longitude[0]))
