"""
This file contains sensor calibration utilities
"""


class SetGyros:
    """
    This is for calibrating the backup IMU in addition to the realtime 9DOF.
    """
    def __init__(self, controller):
        self.controller = controller
        self.dof = self.controller.dof
        self.imu = self.controller.gac.imu
        self.report = None
        self.status = None
        self.magXmin = 32767
        self.magYmin = 32767
        self.magZmin = 32767
        self.magXmax = -32767
        self.magYmax = -32767
        self.magZmax = -32767

    def track(self):
        """
        This tracks the IMU and stores the values to settings.
        """
        MAGx = self.imu.readMAGx()
        MAGy = self.imu.readMAGy()
        MAGz = self.imu.readMAGz()

        if MAGx > self.magXmax:
            self.magXmax = MAGx
        if MAGy > self.magYmax:
            self.magYmax = MAGy
        if MAGz > self.magZmax:
            self.magZmax = MAGz

        if MAGx < self.magXmin:
            self.magXmin = MAGx
        if MAGy < self.magYmin:
            self.magYmin = MAGy
        if MAGz < self.magZmin:
            self.magZmin = MAGz

        sett = self.controller.settings
        sett.set('magXmin', self.magXmin)
        sett.set('magXmax', self.magXmax)
        sett.set('magYmin', self.magYmin)
        sett.set('magYmax', self.magYmax)
        sett.set('magZmin', self.magZmin)
        sett.set('magZmax', self.magZmax)
        self.report = [
            'xmi: ' + str(self.magXmin),
            'xma: ' + str(self.magXmax),
            'ymi: ' + str(self.magYmin),
            'ymi: ' + str(self.magYmin),
            'zmi: ' + str(self.magZmin),
            'zmi: ' + str(self.magZmin),
        ]
        self.dof.fetch_constants()
        self.status = self.dof.calibration_status
        return self
