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
        s = self.sensor = BNO.BNO055()
        print(type(self.controller.settings.dof_remap), self.controller.settings.dof_remap)
        mapp, sign = self.controller.settings.dof_remap
        s.set_axis_remap_raw(mapp, sign)
        self.calibrations = self.controller.settings.dof_calibrations
        self.is_calibrated = True
        if not self.calibrations:
            print('no calibrations found, creating...')
            self.is_calibrated = False
            self.reset_calibration()
        self.readings = [
            # 'temp',
            'accelerometer',
            # 'magnetometer',
            # 'gyroscope',
            'euler',
            'quaternion',
            'linear_acceleration',
            # 'gravity'
        ]
        self.status = self.calibration_status = None
        self.reading = None

    def fetch_constants(self):
        """
        This pulls static data from the chip
        """
        self.status = self.sensor.get_system_status()
        calibration_status = self.sensor.get_calibration_status()
        if calibration_status == (3, 3, 3, 3):
            self.is_calibrated = True
        else:
            self.is_calibrated = False
        sys, gyr, acc, mag = calibration_status
        self.calibration_status = 'sy: ' + str(sys) + ' gy: ' + str(gyr) + ' ac: ' + str(acc) + ' ma: ' + str(mag)

    def reset_calibration(self):
        """
        We can use this to recover the state after we fail to load an invalid calibration.
        """
        self.calibrations = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 252, 255, 251, 255, 1, 0, 232, 3, 0, 0]
        self.sensor.set_calibration(
            self.calibrations
        )
        self.save_calibration()

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
        self.calibrations = self.controller.settings.dof_calibrations
        if self.calibrations:
            self.sensor.set_calibration(
                self.calibrations
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
