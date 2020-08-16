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
import pprint
from warehouse.utils import check_dict
from warehouse.system import get_cpu_temperature, get_system_stats
from warehouse.communication import NetScan


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
        self.temp = get_cpu_temperature  # Pull CPU temps.
        self.stats = get_system_stats  # Read system info.
        self.adc = ADCPi(*settings.ADC_I2C)  # Init ADC.
        self.adc.set_pga(1)  # Set gain.
        self.adc.set_bit_rate(12)  # Adjust timing (lower is faster).
        self.adc.set_conversion_mode(1)  # Set continuous conversion.
        self.netscan = NetScan

        self.threads = [  # Create threads.
            Thread(target=self.read_adc, args=()),
            Thread(target=self.read_imu, args=()),
            Thread(target=self.read_system, args=()),
            Thread(target=self.read_networks, args=()),
            Thread(target=self.read_gps, args=()),
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
            try:
                if not settings.Debug_Pretty:
                    for reading in self.rt_data:
                        print(reading, self.rt_data[reading], '\n')
                else:
                    pprint.PrettyPrinter(indent=4).pprint(self.rt_data)
            except RuntimeError:
                pass
            time.sleep(settings.Debug_Cycle)

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
            imud['ACCEL'] = self.gac(3).acceleration
            imud['GYRO'] = self.gac(2).gyro
            imud['MAG'] = self.gac(3).magnetic
            imud['TEMP'] = self.gac().temp
            imud['ALT'] = self.alt().pressure
            self.rt_data['IMU'] = imud

    def read_system(self):
        """
        This is where we read values in relation to the running system itself.
        """
        sys = check_dict(self.rt_data, 'SYS')
        while not self.term:
            sys['CPU_TEMP'] = self.temp()
            sys['STATS'] = self.stats()
            time.sleep(settings.System_Cycle)

    def read_networks(self):
        """
        This is where we perform out wireless network scans. This is placed here because it takes longer to run depending
        on the amount of information that neads to be read.
        """
        sys = check_dict(self.rt_data, 'SYS')
        while not self.term:
            sys['NETWORKS'] = self.netscan().data
            time.sleep(settings.NetScan_Cycle)

    def read_gps(self):
        """
        Here is where we gather GPS location data.
        """
        gps = check_dict(self.rt_data, 'GPS')
        while not self.term:
            if GPIO.input(settings.Gps_Sync):
                gps_dat = self.gps().getpositiondata()
                gps['LAT'] = gps_dat.lat
                gps['LONG'] = gps_dat.long
        time.sleep(0.1)
