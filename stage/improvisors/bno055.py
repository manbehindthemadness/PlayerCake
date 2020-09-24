"""
This is where we will keep our real time gyro code.

https://github.com/adafruit/Adafruit_Python_BNO055/blob/master/examples/simpletest.py
"""

import logging

from Adafruit_BNO055 import BNO055 as BNO

logger = logging.getLogger('Adafruit_BNO055.BNO055')
logger.setLevel('WARNING')


class BNO055:
    """
    This is where we will read our real-time 9dof sensor.
    """
    def __init__(self, controller):
        self.controller = controller
        self.data = self.controller.rt_data['9DOF']
        self.sensor = BNO.BNO055()
        self.readings = [
            'temp',
            'accelerometer',
            'magnetometer',
            'gyroscope',
            'euler',
            'quaternion',
            'linear_acceleration',
            'gravity'
        ]
        self.reading = None

    def read(self):
        """
        This reads the 9dof data and adds it into the real time data model.
        """
        for reading in self.readings:
            exec('self.reading = self.sensor.read_' + reading + '()')
            # print(self.reading)
            self.data[reading] = self.reading
