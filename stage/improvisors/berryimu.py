"""
Here we have our class for reading and filtering the BerryIMU module.
"""

import math
import datetime
import time
import smbus2 as smbus
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
        ] + settings.IMU_rt_values

    def getvalues(self):
        """
        Fetches filtered information from IMU.
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


# define BMP388 Device I2C address

I2C_ADD_BMP388_AD0_LOW = 0x76
I2C_ADD_BMP388_AD0_HIGH = 0x77
I2C_ADD_BMP388 = I2C_ADD_BMP388_AD0_HIGH

BMP388_REG_ADD_WIA = 0x00
BMP388_REG_VAL_WIA = 0x50

BMP388_REG_ADD_ERR = 0x02
BMP388_REG_VAL_FATAL_ERR = 0x01
BMP388_REG_VAL_CMD_ERR = 0x02
BMP388_REG_VAL_CONF_ERR = 0x04

BMP388_REG_ADD_STATUS = 0x03
BMP388_REG_VAL_CMD_RDY = 0x10
BMP388_REG_VAL_DRDY_PRESS = 0x20
BMP388_REG_VAL_DRDY_TEMP = 0x40

BMP388_REG_ADD_CMD = 0x7E
BMP388_REG_VAL_EXTMODE_EN = 0x34
BMP388_REG_VAL_FIFI_FLUSH = 0xB0
BMP388_REG_VAL_SOFT_RESET = 0xB6

BMP388_REG_ADD_PWR_CTRL = 0x1B
BMP388_REG_VAL_PRESS_EN = 0x01
BMP388_REG_VAL_TEMP_EN = 0x02
BMP388_REG_VAL_NORMAL_MODE = 0x30

BMP388_REG_ADD_PRESS_XLSB = 0x04
BMP388_REG_ADD_PRESS_LSB = 0x05
BMP388_REG_ADD_PRESS_MSB = 0x06
BMP388_REG_ADD_TEMP_XLSB = 0x07
BMP388_REG_ADD_TEMP_LSB = 0x08
BMP388_REG_ADD_TEMP_MSB = 0x09

BMP388_REG_ADD_T1_LSB = 0x31
BMP388_REG_ADD_T1_MSB = 0x32
BMP388_REG_ADD_T2_LSB = 0x33
BMP388_REG_ADD_T2_MSB = 0x34
BMP388_REG_ADD_T3 = 0x35
BMP388_REG_ADD_P1_LSB = 0x36
BMP388_REG_ADD_P1_MSB = 0x37
BMP388_REG_ADD_P2_LSB = 0x38
BMP388_REG_ADD_P2_MSB = 0x39
BMP388_REG_ADD_P3 = 0x3A
BMP388_REG_ADD_P4 = 0x3B
BMP388_REG_ADD_P5_LSB = 0x3C
BMP388_REG_ADD_P5_MSB = 0x3D
BMP388_REG_ADD_P6_LSB = 0x3E
BMP388_REG_ADD_P6_MSB = 0x3F
BMP388_REG_ADD_P7 = 0x40
BMP388_REG_ADD_P8 = 0x41
BMP388_REG_ADD_P9_LSB = 0x42
BMP388_REG_ADD_P9_MSB = 0x43
BMP388_REG_ADD_P10 = 0x44
BMP388_REG_ADD_P11 = 0x45


class ReadAlt(object):
    """docstring for BMP388"""

    def __init__(self, address=I2C_ADD_BMP388):
        self._address = address
        self._bus = smbus.SMBus(0x01)

        self.T_fine = None
        self.altitude = None
        self.temperature = None
        self.pressure = None
        # Load calibration values.

        if self._read_byte(BMP388_REG_ADD_WIA) == BMP388_REG_VAL_WIA:
            print("Pressure sersor is BMP388!\r\n")
            u8RegData = self._read_byte(BMP388_REG_ADD_STATUS)
            if u8RegData & BMP388_REG_VAL_CMD_RDY:
                self._write_byte(BMP388_REG_ADD_CMD,
                                 BMP388_REG_VAL_SOFT_RESET)
                time.sleep(0.01)
        else:
            print("Pressure sersor NULL!\r\n")
        self._write_byte(BMP388_REG_ADD_PWR_CTRL,
                         BMP388_REG_VAL_PRESS_EN
                         | BMP388_REG_VAL_TEMP_EN
                         | BMP388_REG_VAL_NORMAL_MODE)
        self._load_calibration()

    def _read_byte(self, cmd):
        return self._bus.read_byte_data(self._address, cmd)

    def _read_s8(self, cmd):
        result = self._read_byte(cmd)
        if result > 128:
            result -= 256
        return result

    def _read_u16(self, cmd):
        LSB = self._bus.read_byte_data(self._address, cmd)
        MSB = self._bus.read_byte_data(self._address, cmd + 0x01)
        return (MSB << 0x08) + LSB

    def _read_s16(self, cmd):
        result = self._read_u16(cmd)
        if result > 32767:
            result -= 65536
        return result

    def _write_byte(self, cmd, val):
        self._bus.write_byte_data(self._address, cmd, val)

    def _load_calibration(self):
        """
        Set initial variables.
        """
        self.T1 = self._read_u16(BMP388_REG_ADD_T1_LSB)
        self.T2 = self._read_u16(BMP388_REG_ADD_T2_LSB)
        self.T3 = self._read_s8(BMP388_REG_ADD_T3)
        self.P1 = self._read_s16(BMP388_REG_ADD_P1_LSB)
        self.P2 = self._read_s16(BMP388_REG_ADD_P2_LSB)
        self.P3 = self._read_s8(BMP388_REG_ADD_P3)
        self.P4 = self._read_s8(BMP388_REG_ADD_P4)
        self.P5 = self._read_u16(BMP388_REG_ADD_P5_LSB)
        self.P6 = self._read_u16(BMP388_REG_ADD_P6_LSB)
        self.P7 = self._read_s8(BMP388_REG_ADD_P7)
        self.P8 = self._read_s8(BMP388_REG_ADD_P8)
        self.P9 = self._read_s16(BMP388_REG_ADD_P9_LSB)
        self.P10 = self._read_s8(BMP388_REG_ADD_P10)
        self.P11 = self._read_s8(BMP388_REG_ADD_P11)

    def compensate_temperature(self, adc_t):
        """
        Calculates temperature offsets.
        """
        partial_data1 = adc_t - 256 * self.T1
        partial_data2 = self.T2 * partial_data1
        partial_data3 = partial_data1 * partial_data1
        partial_data4 = partial_data3 * self.T3
        partial_data5 = partial_data2 * 262144 + partial_data4
        partial_data6 = partial_data5 / 4294967296
        self.T_fine = partial_data6
        comp_temp = partial_data6 * 25 / 16384
        return comp_temp

    def compensate_pressure(self, adc_p):
        """
        Calculates pressure offsets.
        """
        partial_data1 = self.T_fine * self.T_fine
        partial_data2 = partial_data1 / 0x40
        partial_data3 = partial_data2 * self.T_fine / 256
        partial_data4 = self.P8 * partial_data3 / 0x20
        partial_data5 = self.P7 * partial_data1 * 0x10
        partial_data6 = self.P6 * self.T_fine * 4194304
        offset = self.P5 * 140737488355328 + partial_data4 \
            + partial_data5 + partial_data6

        partial_data2 = self.P4 * partial_data3 / 0x20
        partial_data4 = self.P3 * partial_data1 * 0x04
        partial_data5 = (self.P2 - 16384) * self.T_fine * 2097152
        sensitivity = (self.P1 - 16384) * 70368744177664 \
            + partial_data2 + partial_data4 + partial_data5

        partial_data1 = sensitivity / 16777216 * adc_p
        partial_data2 = self.P10 * self.T_fine
        partial_data3 = partial_data2 + 65536 * self.P9
        partial_data4 = partial_data3 * adc_p / 8192
        partial_data5 = partial_data4 * adc_p / 512
        partial_data6 = adc_p * adc_p
        partial_data2 = self.P11 * partial_data6 / 65536
        partial_data3 = partial_data2 * adc_p / 128
        partial_data4 = offset / 0x04 + partial_data1 + partial_data5 \
            + partial_data3
        comp_press = partial_data4 * 25 / 1099511627776
        return comp_press

    def get_temperature_and_pressure_and_altitude(self):
        """Returns pressure in Pa as double. Output value of "6386.2"equals 96386.2 Pa = 963.862 hPa."""

        xlsb = self._read_byte(BMP388_REG_ADD_TEMP_XLSB)
        lsb = self._read_byte(BMP388_REG_ADD_TEMP_LSB)
        msb = self._read_byte(BMP388_REG_ADD_TEMP_MSB)
        adc_T = (msb << 0x10) + (lsb << 0x08) + xlsb
        self.temperature = self.compensate_temperature(adc_T)
        xlsb = self._read_byte(BMP388_REG_ADD_PRESS_XLSB)
        lsb = self._read_byte(BMP388_REG_ADD_PRESS_LSB)
        msb = self._read_byte(BMP388_REG_ADD_PRESS_MSB)

        adc_P = (msb << 0x10) + (lsb << 0x08) + xlsb
        self.pressure = self.compensate_pressure(adc_P)
        self.altitude = 4433000 * (0x01 - pow(self.pressure / 100.0 / 101325.0, 0.1903))

        return self
