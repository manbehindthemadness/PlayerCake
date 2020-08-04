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
    def __init__(self, dec=None):
        """

        :param dec: clamp the decimal place of the readouts.
        """
        self.dec = dec
        # Read acceleration, magnetometer, gyroscope, temperature.
        self.acceleration = list(sensor.acceleration)
        self.magnetic = list(sensor.magnetic)
        self.gyro = list(sensor.gyro)
        self.temp = sensor.temperature
        if dec:
            self.acceleration = self.scope_decimal(self.acceleration)
            self.magnetic = self.scope_decimal(self.magnetic)
            self.gyro = self.scope_decimal(self.gyro)

    def scope_decimal(self, measurement):
        """
        Rounds floats to a specific decimal place.
        :param measurement: Measurement from the sensor.
        :type measurement: Map
        :return: Array of measurements.
        :rtype: list
        """
        for idx, reading in enumerate(measurement):
            measurement[idx] = round(reading, self.dec)
        return measurement
