"""
Here we have our class for reading and filtering the BerryIMU module.
"""

import math
import datetime

from stage import settings
from stage.improvisors import IMU


class ReadIMU(object):
    """
    Fetches and filters IMU data.
    """
    def __init__(self):
        IMU.detectIMU()  # Detect if BerryIMUv1 or BerryIMUv2 is connected.
        IMU.initIMU()  # Initialise the accelerometer, gyroscope and compass
        self.cycle_start_time = datetime.datetime.now()
        self.cycle_time = 0.0
        self.LP = None
        self.ACCy = None
        self.ACCx = None
        self.ACCz = None
        self.GYRx = None
        self.GYRy = None
        self.GYRz = None
        self.MAGx = None
        self.MAGy = None
        self.MAGz = None
        self.AccXangle = None
        self.AccYangle = None
        self.rate_gyr_x = None
        self.rate_gyr_y = None
        self.rate_gyr_z = None
        self.pitch = None
        self.roll = None
        self.heading = None
        self.magXcomp = None
        self.magYcomp = None
        self.tiltCompensatedHeading = None
        # Pull stuff from settings file (we do this so we can easily adjust calibration settings).
        self.magXmin = settings.magXmin
        self.magYmin = settings.magYmin
        self.magZmin = settings.magZmin
        self.magXmax = settings.magXmax
        self.magYmax = settings.magYmax
        self.magZmax = settings.magZmax
        self.G_GAIN = settings.G_GAIN
        self.gyroXangle = settings.gyroXangle
        self.gyroYangle = settings.gyroYangle
        self.gyroZangle = settings.gyroZangle
        self.IMU_UPSIDE_DOWN = settings.IMU_UPSIDE_DOWN
        self.RAD_TO_DEG = settings.RAD_TO_DEG
        self.M_PI = settings.M_PI
        self.AA = settings.AA
        self.KFangleX = settings.KFangleX
        self.KFangleY = settings.KFangleY
        self.CFangleX = settings.CFangleX
        self.CFangleY = settings.CFangleY
        self.kalmanX = settings.kalmanX
        self.kalmanY = settings.kalmanY
        self.Q_angle = settings.Q_angle
        self.Q_gyro = settings.Q_gyro
        self.R_angle = settings.R_angle
        self.y_bias = settings.y_bias
        self.x_bias = settings.x_bias
        self.XP_00 = settings.XP_00
        self.XP_01 = settings.XP_01
        self.XP_10 = settings.XP_10
        self.XP_11 = settings.XP_11
        self.YP_00 = settings.YP_00
        self.YP_01 = settings.YP_01
        self.YP_10 = settings.YP_10
        self.YP_11 = settings.YP_11

        self.rt_values = [
            'AccXangle',
            'AccYangle',
            'gyroXangle',
            'gyroYangle',
            'gyroZangle',
            'CFangleX',
            'CFangleY',
            'heading',
            'tiltCompensatedHeading',
            'kalmanX',
            'kalmanY'
        ]

    def getvalues(self):
        """
        Fetches filtered information from IMU
        """

        # Read the accelerometer,gyroscope and magnetometer values
        self.ACCx = IMU.readACCx()
        self.ACCy = IMU.readACCy()
        self.ACCz = IMU.readACCz()
        self.GYRx = IMU.readGYRx()
        self.GYRy = IMU.readGYRy()
        self.GYRz = IMU.readGYRz()
        self.MAGx = IMU.readMAGx()
        self.MAGy = IMU.readMAGy()
        self.MAGz = IMU.readMAGz()

        # Apply compass calibration
        self.MAGx -= (self.magXmin + self.magXmax) / 2
        self.MAGy -= (self.magYmin + self.magYmax) / 2
        self.MAGz -= (self.magZmin + self.magZmax) / 2

        # Calculate loop Period(LP). How long between Gyro Reads

        self.cycle_time = datetime.datetime.now() - self.cycle_start_time
        self.cycle_start_time = datetime.datetime.now()
        self.LP = self.cycle_time.microseconds / (1000000 * 1.0)

        # Convert Gyro raw to degrees per second
        self.rate_gyr_x = self.GYRx * self.G_GAIN
        self.rate_gyr_y = self.GYRy * self.G_GAIN
        self.rate_gyr_z = self.GYRz * self.G_GAIN

        # Calculate the angles from the gyro.
        self.gyroXangle += self.rate_gyr_x * self.LP
        self.gyroYangle += self.rate_gyr_y * self.LP
        self.gyroZangle += self.rate_gyr_z * self.LP

        # Convert Accelerometer values to degrees

        if not self.IMU_UPSIDE_DOWN:
            # If the IMU is up the correct way (Skull logo facing down), use these calculations
            self.AccXangle = (math.atan2(self.ACCy, self.ACCz) * self.RAD_TO_DEG)
            self.AccYangle = (math.atan2(self.ACCz, self.ACCx) + self.M_PI) * self.RAD_TO_DEG
        else:
            # Us these four lines when the IMU is upside down. Skull logo is facing up
            self.AccXangle = (math.atan2(-self.ACCy, -self.ACCz) * self.RAD_TO_DEG)
            self.AccYangle = (math.atan2(-self.ACCz, -self.ACCx) + self.M_PI) * self.RAD_TO_DEG

        # Change the rotation value of the accelerometer to -/+ 180 and
        # move the Y axis '0' point to up.  This makes it easier to read.
        if self.AccYangle > 90:
            self.AccYangle -= 270.0
        else:
            self.AccYangle += 90.0

        # Complementary filter used to combine the accelerometer and gyro values.
        self.CFangleX = self.AA * (self.CFangleX + self.rate_gyr_x * self.LP) + (1 - self.AA) * self.AccXangle
        self.CFangleY = self.AA * (self.CFangleY + self.rate_gyr_y * self.LP) + (1 - self.AA) * self.AccYangle

        # Kalman filter used to combine the accelerometer and gyro values.
        self.kalmanY = self.kalmanfiltery()
        self.kalmanX = self.kalmanfilterx()

        if self.IMU_UPSIDE_DOWN:
            self.MAGy = -self.MAGy  # If IMU is upside down, this is needed to get correct heading.
        # Calculate heading
        self.heading = 180 * math.atan2(self.MAGy, self.MAGx) / self.M_PI

        # Only have our heading between 0 and 360
        if self.heading < 0:
            self.heading += 360

        # Tilt compensated heading#########################

        # Normalize accelerometer raw values.
        if not self.IMU_UPSIDE_DOWN:
            # Use these two lines when the IMU is up the right way. Skull logo is facing down
            accXnorm = self.ACCx / math.sqrt(self.ACCx * self.ACCx + self.ACCy * self.ACCy + self.ACCz * self.ACCz)
            accYnorm = self.ACCy / math.sqrt(self.ACCx * self.ACCx + self.ACCy * self.ACCy + self.ACCz * self.ACCz)
        else:
            # Us these four lines when the IMU is upside down. Skull logo is facing up
            accXnorm = -self.ACCx / math.sqrt(self.ACCx * self.ACCx + self.ACCy * self.ACCy + self.ACCz * self.ACCz)
            accYnorm = self.ACCy / math.sqrt(self.ACCx * self.ACCx + self.ACCy * self.ACCy + self.ACCz * self.ACCz)

        # Calculate pitch and roll

        self.pitch = math.asin(accXnorm)
        self.roll = -math.asin(accYnorm / math.cos(self.pitch))

        # Calculate the new tilt compensated values
        self.magXcomp = self.MAGx * math.cos(self.pitch) + self.MAGz * math.sin(self.pitch)

        # The compass and accelerometer are orientated differently on the LSM9DS0 and LSM9DS1 and the Z axis on the compass
        # is also reversed. This needs to be taken into consideration when performing the calculations
        if IMU.LSM9DS0:
            self.magYcomp = self.MAGx * math.sin(self.roll) * math.sin(self.pitch) + self.MAGy * math.cos(self.roll) - self.MAGz * math.sin(
                self.roll) * math.cos(
                self.pitch)  # LSM9DS0
        else:
            self.magYcomp = self.MAGx * math.sin(self.roll) * math.sin(self.pitch) + self.MAGy * math.cos(self.roll) + self.MAGz * math.sin(
                self.roll) * math.cos(
                self.pitch)  # LSM9DS1

        # Calculate tilt compensated heading
        self.tiltCompensatedHeading = 180 * math.atan2(self.magYcomp, self.magXcomp) / self.M_PI

        if self.tiltCompensatedHeading < 0:
            self.tiltCompensatedHeading += 360

        # END ##################################

        return self

    # noinspection DuplicatedCode
    def kalmanfiltery(self):
        """
        Berry GPS Filter for Y
        """

        self.KFangleY = self.KFangleY + self.LP * (self.rate_gyr_y - self.y_bias)

        self.YP_00 = self.YP_00 + (- self.LP * (self.YP_10 + self.YP_01) + self.Q_angle * self.LP)
        self.YP_01 = self.YP_01 + (- self.LP * self.YP_11)
        self.YP_10 = self.YP_10 + (- self.LP * self.YP_11)
        self.YP_11 = self.YP_11 + (+ self.Q_gyro * self.LP)

        y = self.AccYangle - self.KFangleY
        S = self.YP_00 + self.R_angle
        K_0 = self.YP_00 / S
        K_1 = self.YP_10 / S

        self.KFangleY = self.KFangleY + (K_0 * y)
        self.y_bias = self.y_bias + (K_1 * y)

        self.YP_00 = self.YP_00 - (K_0 * self.YP_00)
        self.YP_01 = self.YP_01 - (K_0 * self.YP_01)
        self.YP_10 = self.YP_10 - (K_1 * self.YP_00)
        self.YP_11 = self.YP_11 - (K_1 * self.YP_01)

        return self.KFangleY

    # noinspection DuplicatedCode
    def kalmanfilterx(self):
        """
        Berry GPS Filter for X
        """

        self.KFangleX = self.KFangleX + self.LP * (self.AccXangle - self.x_bias)

        self.XP_00 = self.XP_00 + (- self.LP * (self.XP_10 + self.XP_01) + self.Q_angle * self.LP)
        self.XP_01 = self.XP_01 + (- self.LP * self.XP_11)
        self.XP_10 = self.XP_10 + (- self.LP * self.XP_11)
        self.XP_11 = self.XP_11 + (+ self.Q_gyro * self.LP)

        x = self.AccXangle - self.KFangleX
        S = self.XP_00 + self.R_angle
        K_0 = self.XP_00 / S
        K_1 = self.XP_10 / S

        self.KFangleX = self.KFangleX + (K_0 * x)
        self.x_bias = self.x_bias + (K_1 * x)

        self.XP_00 = self.XP_00 - (K_0 * self.XP_00)
        self.XP_01 = self.XP_01 - (K_0 * self.XP_01)
        self.XP_10 = self.XP_10 - (K_1 * self.XP_00)
        self.XP_11 = self.XP_11 - (K_1 * self.XP_01)

        return self.KFangleX
