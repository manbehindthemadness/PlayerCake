"""
This file contains the realtime sensor loop.
"""

from stage import settings
from stage.improvisors.berryimu import read_berry
from ADCPi import ADCPi
import RPi.GPIO as GPIO
import os
import datetime
from warehouse.system import get_cpu_temperature

# noinspection PyArgumentEqualDefault,PyArgumentEqualDefault,PyArgumentEqualDefault
adc = ADCPi(*settings.ADC_I2C)  # Init ADC.
adc.set_pga(1)  # Set gain
adc.set_bit_rate(12)  # Adjust timing (lower is faster)
adc.set_conversion_mode(1)  # Set continuous conversion


if settings.Debug:
    GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(settings.Cooling_Fan, GPIO.OUT)  # Init cooling fan.
GPIO.output(settings.Cooling_Fan, 0)

temp = 0.0
cnt = 0
while True:
    if cnt > 10:
        cnt = 0
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

    # Read gyro, accel, compass.
    GAC = read_berry(datetime.datetime.now())

    if settings.Debug and not cnt:
        message = 'ADC INPUT: ' + str(adc_output) + '\nGAC: ' + GAC + '\n' + str(temp)
        print(message)

    cnt += 1
