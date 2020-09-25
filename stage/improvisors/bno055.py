"""
This is where we will keep our real time gyro code.

https://github.com/adafruit/Adafruit_Python_BNO055/blob/master/examples/simpletest.py
"""

import logging

from stage.oem.Adafruit_BNO055 import BNO055 as BNO

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
        self.status = self.calibration_status = None
        self.reading = None

    def fetch_constants(self):
        """
        This pulls static data from the chip
        """
        self.status = self.sensor.get_system_status()
        self.calibration_status = self.sensor.get_calibration_status()

    def reset_calibration(self):
        """
        We can use this to recover the state after we fail to load an invalid calibration.
        """
        self.sensor.set_calibration(
            [87, 67, 87, 56, 53, 13, 34, 87, 66, 76, 4, 87, 67, 54, 252, 255, 255, 255, 232, 3, 5, 3]
        )

    def save_calibration(self):
        """
        This will save the calibration data to our settings file.
        """

        self.controller.settings.set(
            'dof_calibrations',
            self.sensor.get_calibration()
        )
        self.controller.settings.save()

    def load_calibration(self):
        """
        This reads out calibration from the settings file and loads it into the 9dof.
        """
        calibrations = self.controller.settings.dof_calibrations
        if calibrations:
            self.sensor.set_calibration(
                calibrations
            )

    def read(self):
        """
        This reads the 9dof data and adds it into the real time data model.
        """
        for idx, reading in enumerate(self.readings):
            exec('self.reading = self.sensor.read_' + reading + '()')
            # print(self.reading)
            self.data[reading] = self.reading
        readings = list()
        for reading in self.data:
            data = self.data[reading]
            if isinstance(data, tuple):
                for value in list(data):
                    if value:
                        readings.append(value)
        if not readings:
            self.reset_calibration()

