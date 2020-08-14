"""
This is where we will read our altimeter/pressure sensor.
"""

import board
import busio
from stage.oem.bmp280 import adafruit_bmp280
i2c = busio.I2C(board.SCL, board.SDA)


def alt():
    """
    Returns our handy sensor.
    """
    return adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
