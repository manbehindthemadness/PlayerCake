"""
This is our ADC code.


Timeit values from tests.adc:

single: 9.833299554884434e-05
all: 0.0004996329953428358
both: 0.0008892149926396087


"""
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from warehouse.math import average


class MCP3008:
    """
    This is where we will read the ADC data and update the real time data model.

    TODO: We need to add filtration to this, probably a kalman.

    TODO: Aslo we need to reduce the names to just the channel number.
    """
    def __init__(self, controller):
        self.complex_filter = False
        self.controller = controller
        self.settings = self.controller.settings
        self.rt_data = self.controller.rt_data
        self.mcp_1 = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0, 0))  # port, device, max_speed_hz=500000
        self.mcp_2 = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0, 1))
        self.reading = None
        self.filtered_ports = None
        self.depth = None
        self.samples = dict()
        self.refresh()

    def refresh(self):
        """
        This refreshes the ADC configs.
        """
        self.depth = self.settings.adc_filter_depth
        self.filtered_ports = self.settings.filtered_adc_ports
        for port in self.filtered_ports:
            self.samples[str(port)] = list()

    def store_sample(self, port, reading):
        """
        This will store a reading into the samples dictionary so it can be evaluated by our kalman filter.
        """
        if self.complex_filter:
            samples = self.samples[str(port)]
            samples.append(reading)
            self.samples[str(port)] = samples[-self.depth:]
        else:
            self.reading = reading

    def get_filtered_sample(self, port):
        """
        This will fetch a sample array, send it through the kalman filter and return the result.
        """
        if self.complex_filter:
            samples = self.samples[str(port)]
            sample = average(samples)
            print(sample, samples[-1:])
            result = round(sample)
        else:
            result = self.normalize_sample(self.reading)
        return result

    @staticmethod
    def normalize_sample(sample):
        """
        SHaves everything but the first two digits.
        """
        return int(str(sample)[0:2])

    def scan(self):
        """
        Scans the adc inputs.
        """
        idx = 0
        for value in range(2):
            if not value:
                for reading in range(8):
                    measurement = self.mcp_1.read_adc(reading)
                    if idx in self.filtered_ports:
                        self.store_sample(idx, measurement)
                        measurement = self.get_filtered_sample(idx)
                    self.controller.rt_data['ADC'][str(idx)] = measurement
                    idx += 1
            else:
                for reading in range(8):
                    measurement = self.mcp_2.read_adc(reading)
                    if idx in self.filtered_ports:
                        self.store_sample(idx, measurement)
                        measurement = self.get_filtered_sample(idx)
                    self.controller.rt_data['ADC'][str(idx)] = measurement
                    idx += 1
            time.sleep(self.controller.settings.adc_cycle)
