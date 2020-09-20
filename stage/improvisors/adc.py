"""
This is our ADC code.
"""
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

chip_1 = digitalio.DigitalInOut(board.D5)
chip_2 = digitalio.DigitalInOut(board.D4)

mcp_1 = MCP.MCP3008(spi, chip_1)
mcp_2 = MCP.MCP3008(spi, chip_2)

channels = []
for mcp in [mcp_1, mcp_2]:
    for channelnum in range(8):
        channel = AnalogIn(mcp, eval('MCP.P' + str(channelnum)))
        channels.append(channel)


class MCP3008:
    """
    This is where we will read the ADC data and update the real time data model.
    """
    def __init__(self, controller):
        for idx, chan in enumerate(channels):
            comp = 0
            if idx in controller.settings.adc_ungrounded_channels:
                comp = controller.settings.adc_noise
            controller.rt_data['ADC']['ADCPort' + str(idx)] = (chan.value - comp)  # We might need to change this to voltage.
