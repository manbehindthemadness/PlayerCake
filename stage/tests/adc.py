"""
Test file for the Raspi ADC module
"""
import busio
import digitalio
import board
import timeit
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


def constant_test():
    """
    This tests constantly until the program is interrupted.
    """

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


def time_test():
    """
    This tests to see how long it takes us to measure a single input.
    """
    def measure_single():
        """
        Performs measurement action.
        """
        for adc in range(1):
            AnalogIn(mcp, eval('MCP.P' + str(adc)))

    def measure_all():
        """
        This measures all the inputs on a single mm3008 chip.
        """

        for adc in range(8):
            AnalogIn(mcp, eval('MCP.P' + str(adc)))

    def measure_both():
        """
        This measures all inputs across both m3008 chips.
        """
        for adc in range(8):
            AnalogIn(mcp, eval('MCP.P' + str(adc)))
            AnalogIn(mcpp, eval('MCP.P' + str(adc)))

    print('single:', timeit.timeit(lambda: measure_single(), number=1))

    print('all:', timeit.timeit(lambda: measure_all(), number=1))

    print('both:', timeit.timeit(lambda: measure_both(), number=1))
