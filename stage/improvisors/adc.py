"""
This is our ADC code.
"""
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008


class MCP3008:
    """
    This is where we will read the ADC data and update the real time data model.
    """
    def __init__(self, controller):
        self.controller = controller

        self.mcp_1 = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0, 0))
        self.mcp_2 = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0, 1))

    def scan(self):
        """
        Scans the adc inputs.
        """
        idx = 0
        for value in range(2):
            if not value:
                for reading in range(8):
                    self.controller.rt_data['ADC']['ADCPort' + str(idx)] = self.mcp_1.read_adc(reading)
                    idx += 1
            else:
                for reading in range(8):
                    self.controller.rt_data['ADC']['ADCPort' + str(idx)] = self.mcp_2.read_adc(reading)
                    idx += 1
            time.sleep(self.controller.settings.adc_cycle)
