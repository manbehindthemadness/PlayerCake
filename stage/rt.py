"""
This file contains the realtime sensor loop.
"""

from stage import settings
from ADCPi import ADCPi
from stage.oem.berry_imu import IMU
import RPi.GPIO as GPIO
import time
import datetime
from warehouse.system import get_cpu_temperature

# noinspection PyArgumentEqualDefault,PyArgumentEqualDefault,PyArgumentEqualDefault
adc = ADCPi(*settings.ADC_I2C)  # Init ADC.
adc.set_pga(1)  # Set gain
adc.set_bit_rate(12)  # Adjust timing (lower is faster)
adc.set_conversion_mode(1)  # Set continuous conversion

IMU.detectIMU()  # Detect if BerryIMUv1 or BerryIMUv2 is connected.
IMU.initIMU()  # Initialise the accelerometer, gyroscope and compass

if settings.Debug:
    GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(settings.Cooling_Fan, GPIO.OUT)  # Init cooling fan.
GPIO.output(settings.Cooling_Fan, 0)


clear_screen = ''
for cls in range(1, settings.Debug_Line_Clear):
    clear_screen += '\n'


cnt = 0
while True:
    if not cnt:  # Init cooling.
        temp = get_cpu_temperature()
        if temp >= settings.Cooling_Temp_High:
            GPIO.output(settings.Cooling_Fan, 1)
        elif temp <= settings.Cooling_Temp_Low:
            GPIO.output(settings.Cooling_Fan, 0)

    adc_output = list()  # Read ADC values
    for adc_channel in range(1, settings.ADC_Num_Channels):
        adc_value = adc.read_voltage(adc_channel)
        if adc_channel in settings.ADC_Ungrounded_Channels:  # Clamp noise
            adc_value = adc_value - settings.ADC_Noise
        adc_output.append(adc_value)

    # Read accerometer values.
    ACCx = IMU.readACCx()
    ACCy = IMU.readACCy()
    ACCz = IMU.readACCz()
    accel_output = [
        (ACCx * 0.244)/1000,
        (ACCy * 0.244)/1000,
        (ACCz * 0.244) / 1000
    ]

