"""
This file contains the realtime sensor loop.

TODO: Revise GPS to use circuitpython.
"""

from stage import settings
from stage.improvisors.lsm9ds1 import lsm9ds1
from stage.improvisors.gps_lkp import ReadGPS
from stage.improvisors .bmp280 import alt
from ADCPi import ADCPi
import RPi.GPIO as GPIO
from threading import Thread
import time
from warehouse.system import get_cpu_temperature


# noinspection PyArgumentEqualDefault,PyArgumentEqualDefault,PyArgumentEqualDefault
adc = ADCPi(*settings.ADC_I2C)  # Init ADC.
adc.set_pga(1)  # Set gain
adc.set_bit_rate(12)  # Adjust timing (lower is faster)
adc.set_conversion_mode(1)  # Set continuous conversion

rt_data = dict()
term = False


if settings.Debug:
    GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(settings.Cooling_Fan, GPIO.OUT)  # Init cooling fan.
GPIO.output(settings.Cooling_Fan, 0)
GPIO.setup(settings.Gps_Sync, GPIO.IN)  # Setup GPS sync.
GPIO.setup(settings.Gps_Enable, GPIO.OUT)  # Setup GPS enable.
GPIO.output(settings.Gps_Enable, 1)  # Init GPS to acquire initial fix.


temp = 0.0
cnt = 0
rc = 0
gps = ReadGPS()
position = gps.latlong


class Start:
    """
    Real time program loop.
    """
    def __init__(self):
        global rt_data
        global term
        self.rt_data = rt_data  # Pass realtime data.
        self.term = term  # Pass termination.
        self.gac = lsm9ds1  # Init IMU.
        self.gps = ReadGPS  # Init GPS.
        self.alt = alt  # Init altimiter.
        self.adc = ADCPi(*settings.ADC_I2C)  # Init ADC.
        self.adc.set_pga(1)  # Set gain.
        self.adc.set_bit_rate(12)  # Adjust timing (lower is faster).
        self.adc.set_conversion_mode(1)  # Set continuous conversion.

        self.threads = [  # Create threads.
            Thread(target=self.read_adc, args=()),
            Thread(target=self.read_imu, args=()),
        ]
        if settings.Debug:
            self.threads.append(Thread(target=self.debug, args=()))

        for thread in self.threads:  # Launch threads.
            thread.start()

    def debug(self):
        """
        This dumps the rt_data information to console.
        """
        while not self.term:
            for reading in self.rt_data:
                print(self.rt_data[reading], '\n')
            time.sleep(0.02)

    def read_adc(self):
        """
        Here is where we read the ADC inputs in real-time.
        """
        self.rt_data['ADC'] = dict()
        while not self.term:
            for num in range(1, settings.ADC_Num_Channels):
                comp = 0
                if num in settings.ADC_Ungrounded_Channels:
                    comp = settings.ADC_Noise
                self.rt_data['ADC']['ADCPort' + str(num)] = adc.read_voltage(num - comp)

    def read_imu(self):
        """
        Here is where we read the accel/mag/gyro/alt/temp.
        """
        imud = dict()

        while not self.term:
            imud['ACCEL'] = self.gac().acceleration
            imud['GYRO'] = self.gac().gyro
            imud['MAG'] = self.gac().magnetic
            imud['TEMP'] = self.gac().temp
            imud['ALT'] = self.alt().pressure
            self.rt_data['IMU'] = imud

