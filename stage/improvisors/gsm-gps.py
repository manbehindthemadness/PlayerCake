"""
This is where we will house our minicom GPS and GSM port for the navigation system.

Reference: https://www.hologram.io/references/python-sdk

"""

import serial
import time
import adafruit_gps

base_port = serial.Serial("/dev/ttyACM1", baudrate=115200, timeout=3.0)
gps_port = serial.Serial("/dev/ttyACM3", baudrate=115200, timeout=3.0)
# Enable GPS tunneling.
commands = [
    'AT+UGRMC=1',
    'AT+UGGLL=1',
    'AT+UGGSV=1',
    'AT+UGGGA=1',
    'AT+UGIND=1',
    'AT+UGPRF=1',
    'AT+UGPS=1,1,67'  # AT+UGPS=[mode],[aid_mode],[GNSS_systems]

]
base_port.isOpen()
print(base_port.is_open)
for com in commands:
    com = com.encode() + b'\x0d' + b'\x0a'
    print('sending command', com)
    base_port.write(com)
    time.sleep(0.2)
    info = base_port.readline()
    print('data', repr(info))
base_port.close()
# gps_port.isOpen()

# Read gps data.
gps = adafruit_gps.GPS(gps_port)
while True:
    # info = gps_port.readline()
    # print('data', repr(info))
    gps.update()
    print(gps.latitude, gps.longitude)
    time.sleep(1)
