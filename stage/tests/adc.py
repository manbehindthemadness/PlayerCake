"""
Test file for the Raspi ADC module
"""
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)
css = digitalio.DigitalInOut(board.D4)
# create the mcp object
mcp = MCP.MCP3008(spi, cs)
mcpp = MCP.MCP3008(spi, css)

while True:
    ch = 0
    output1 = []
    output2 = []
    for adc in range(8):
        chan = AnalogIn(mcp, eval('MCP.P' + str(adc)))
        chann = AnalogIn(mcpp, eval('MCP.P' + str(adc)))
        # print(adc)
        # print('Raw ADC Value: ', chan.value)
        # print('ADC Voltage: ' + str(chan.voltage) + 'V')
        #
        # print('Raw ADC Value: ', chann.value)
        # print('ADC Voltage: ' + str(chann.voltage) + 'V')
        output1.append((chan.value, round(chan.voltage, 2)))
        output2.append((chann.value, round(chann.voltage, 2)))
        ch += 1
    print(output1, output2)
