"""
This is the software configuration settings file. These values are general defaults and should be modified in the logal_settings file not here!
"""
Debug = True  # Enables debugging
DirectorID = '6efc1846-d015-11ea-87d0-0242ac130003'  # This ID matches Stage clients to their respective Directors.
Envirnment = 'mixed'  # Mixed means that we are using windows or apple to communicate with Stage: mixed/pure
BindAddr = '0.0.0.0'

# I2C Addresses.

ADC_I2C = (0x68, 0x69, 18)

# Pin assignments.

Cooling_Fan = 12

# Calibrations

ADC_Num_Channels = 8  # Number of ADC channels.
ADC_Noise = 0.002471  # We can use this in the event that the acd chan is not balanced to ground.
ADC_Ungrounded_Channels = []

# If the IMU is upside down (Skull logo facing up), change this value to 1
IMU_UPSIDE_DOWN = 0
RAD_TO_DEG = 57.29578
M_PI = 3.14159265358979323846
G_GAIN = 0.070  # [deg/s/LSB]  If you change the dps for gyro, you need to update this value accordingly
AA = 0.40      # Complementary filter constant

# ################ Compass Calibration values ############
# Use calibrateBerryIMU.py to get calibration values
# Calibrating the compass isnt mandatory, however a calibrated
# compass will result in a more accurate heading value.

magXmin = 0
magYmin = 0
magZmin = 0
magXmax = 0
magYmax = 0
magZmax = 0

'''
Here is an example:
magXmin =  -1748
magYmin =  -1025
magZmin =  -1876
magXmax =  959
magYmax =  1651
magZmax =  708
Dont use the above values, these are just an example.
'''
# Kalman filter variables
Q_angle = 0.02
Q_gyro = 0.0015
R_angle = 0.005
y_bias = 0.0
x_bias = 0.0
XP_00 = 0.0
XP_01 = 0.0
XP_10 = 0.0
XP_11 = 0.0
YP_00 = 0.0
YP_01 = 0.0
YP_10 = 0.0
YP_11 = 0.0
KFangleX = 0.0
KFangleY = 0.0
CFangleX = 0.0
CFangleY = 0.0
# General Settings.

Cooling_Temp_High = 35  # This is the temp where we will enable cooling.
Cooling_Temp_Low = 34  # This is the temp where wil will disable cooling.
