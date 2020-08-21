"""
This is the software configuration settings file. These values are general defaults and should be modified in the logal_settings file not here!
"""
Debug = True  # Enables debugging
Debug_Pretty = False  # Pprint the debug info instead of print. - Disables Debug_filter.
Debug_To_Screen = True  # Report debugging data to the on-board screen.
Screen_template = 'improv'  # Eventually this will allow us to change what the screen is showing.
Debug_Filter = [  # This lists the includes from the real time data model that will be returned to console.
    'GPS',
    'IMU'
]

Role = 'stage'  # This is the role announcement that is used by the network client UDP lookup broadcast.
Target = 'director'  # This is the up-stream role used to direct rebort connections.
DirectorID = '6efc1846-d015-11ea-87d0-0242ac130003'  # This ID matches Stage clients to their respective Directors.
StageID = 'a9b3cfb3-c72d-4efd-993d-6c8dccbb8609'  # This alows us to be identified from other stages.
Environment = 'pure'  # Mixed means that we are using windows or apple to communicate with Stage: mixed/pure
BindAdaptor = 'wlan0'  # This is the network adaptor used to handle incoming and outgoing network traffic.
TCPBindPort = 12001  # TCP listener port.
SSID = ''  # These are placeholder values for when we get QR code recognition working.
Secret = ''

# I2C Addresses.

ADC_I2C = (0x68, 0x69, 18)  # Analog inputs.
PWM = (0x40, 0x70)  # Hardware PWM (Servos)
Accel = 0x6a  # Accelerometer.
Mag = 0x1c  # Compass.
Press = 0x77  # Altimeter/Pressure.
UART = (0x48, 0x90)  # I2C Serial expander (LVMaxSonar, spare).
GPS_UART = '/dev/serial0'  # GPS.
Sonar_UART = '/dev/serial2'  # Digital sonar.
Extra_UART = '/dev/serial3'  # Save for later.

# Pin assignments.

Cooling_Fan = 12  # Optional.
Laser = 16  # Optional.
NV_Flood = 26  # Optional.
Gps_Sync = 13
Gps_Enable = 6
PWM_Enable = 5

# HS-SR04 sonar (Trigger, Echo).
L_Echo = (23, 24)  # Left.
R_Echo = (27, 22)  # Right.
B_Echo = (20, 25)  # Back.

# ADC Pins:
LF_Press = 1  # Left front pressure.
RF_Press = 2  # Right front pressure.
RL_Press = 3  # Rear Left Pressure.
RR_Press = 4  # Right rear pressure.
LF_Z_Pos = 5  # Left front Z position.
RF_Z_Pos = 6  # Right Front Z position.
RL_Z_Pos = 7  # Left rear Z position.
RR_Z_Pos = 8  # Right rear Z position.

# Servos:
LF_X = 0  # Left front X servo.
LF_X_Invert = False  # Reverse X servo.
LF_Y = 1  # Left front Y servo.
LF_Y_Invert = False  # Reverse Y servo.
LF_Z = 2  # Left front Z servo.
LF_Z_Invert = False  # Reverse Z Servo.
LF_Extra = 3  # Extra channel.

RF_X = 4  # Right front X servo.
RF_X_Invert = False  # Reverse X servo.
RF_Y = 5  # Right front Y servo.
RF_Y_Invert = False  # Reverse Y servo.
RF_Z = 6  # Right front Z servo.
RF_Z_Invert = False  # Reverse Z Servo.
RF_Extra = 3  # Extra channel.

LR_X = 8  # Left rear X servo.
LR_X_Invert = False  # Reverse X servo.
LR_Y = 9  # Left rear Y servo.
LR_Y_Invert = False  # Reverse Y servo.
LR_Z = 10  # Left rear Z servo.
LR_Z_Invert = False  # Reverse Z Servo.
LR_Extra = 3  # Extra channel.

RR_X = 12  # Right rear X servo.
RR_X_Invert = False  # Reverse X servo.
RR_Y = 13  # Right rear Y servo.
RR_Y_Invert = False  # Reverse Y servo.
RR_Z = 14  # Right rear Z servo.
RR_Z_Invert = False  # Reverse Z Servo.
RR_Extra = 3  # Extra channel.

# This math will be evaled in the event  we have two servos that need to move in unison (knee and hip for Z lift for example).
X_Solver = ''
Y_SOlver = ''
Z_Solver = ''

# Filters:

# The fades here are used to smooth out noise.
GPS_Fade = 20  # This is the number of samples that we will use to smooth the gps results.
Accel_Fade = 20  # Fade for accelerometer.
Gyro_Fade = 20  # Fade for gyro.
Mag_Fade = 20  # Fade for magnitometer.

# Timings:

Debug_Cycle = 0.02  # Number in seconds to update the debug logs.
NetScan_Cycle = 10  # Number in seconds between updating the list of wireless networks.
System_Cycle = 5  # Time in seconds for updating system information.

# Calibrations

ADC_Num_Channels = 8  # Number of ADC channels.
ADC_Noise = 0.0  # 0.002471  # We can use this in the event that the acd chan is not balanced to ground.
ADC_Ungrounded_Channels = []

# If the IMU is upside down (Skull logo facing up), change this value to 1
IMU_UPSIDE_DOWN = 0
RAD_TO_DEG = 57.29578
M_PI = 3.14159265358979323846
G_GAIN = 0.070  # [deg/s/LSB]  If you change the dps for gyro, you need to update this value accordingly
AA = 0.40      # Complementary filter constant

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

gyroXangle = 0.0
gyroYangle = 0.0
gyroZangle = 0.0
CFangleX = 0.0
CFangleY = 0.0
kalmanX = 0.0
kalmanY = 0.0

IMU_rt_values = []  # Extra variables to be fetched from the IMU may be listed here.

# ################ Compass Calibration values ############
# Use calibrateBerryIMU.py to get calibration values
# Calibrating the compass isnt mandatory, however a calibrated
# compass will result in a more accurate heading value.

magXmin = -871
magYmin = -1112
magZmin = -1786
magXmax = 1666
magYmax = 1132
magZmax = 594

# General Settings.

Cooling_Temp_High = 35  # This is the temp where we will enable cooling.
Cooling_Temp_Low = 34  # This is the temp where wil will disable cooling.
