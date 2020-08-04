"""
Simple demo of the LSM9DS1 accelerometer, magnetometer, gyroscope.
Will print the acceleration, magnetometer, and gyroscope values every second.
"""
import board
import busio
from stage.oem.lsm9ds1 import adafruit_lsm9ds1

# I2C connection:
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)


class lsm9ds1:
    """
    This fires up the accel/gyro/magnetometer/temp device.
    :return: Self
    """
    def __init__(self):
        # Read acceleration, magnetometer, gyroscope, temperature.
        self.acceleration = sensor.acceleration
        self.magnetic = sensor.magnetic
        self.gyro = sensor.gyro
        self.temp = sensor.temperature
