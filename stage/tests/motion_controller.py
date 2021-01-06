"""
This is a simple test to see if our motion controller is working fast enough.

https://github.com/sarfata/pi-blaster
"""
import busio
import digitalio
import board
import timeit
import time
import numpy as np
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
try:
    from stage.actors.bitwizardservo import BWServo
except ImportError:
    # noinspection PyUnresolvedReferences
    from bitwizardservo import BWServo

spi_bus = busio.SPI(clock=board.SCK_1, MISO=board.MISO_1, MOSI=board.MOSI_1)
spi_bus1 = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs0 = digitalio.DigitalInOut(board.D18)
cs1 = digitalio.DigitalInOut(board.D17)
cs2 = digitalio.DigitalInOut(board.CE0)
while not spi_bus.try_lock():
    pass
spi_bus.configure(baudrate=125000000)
spi_bus.unlock()

while not spi_bus1.try_lock():
    pass
spi_bus1.configure(baudrate=100)
spi_bus1.unlock()

mcp0 = MCP.MCP3008(spi_bus, cs0)
mcp1 = MCP.MCP3008(spi_bus, cs1)

# noinspection PyArgumentEqualDefault
bw0 = BWServo(spi_bus1, cs2, 0x86, True)
bw1 = BWServo(spi_bus1, cs2, 0x88, True)
bw0.set_base_freq(496)
bw0.set_base_multiplier(8)
bw1.set_base_freq(496)
bw1.set_base_multiplier(8)


def time_offset(last_time, delay):
    """
    This is an attempt to create a time offset scaler to stabalize our clock.
    """
    def wait(dly):
        """
        This handles the actual delay.
        """
        time.sleep(dly)

    tm = last_time
    varience = np.round(np.subtract(delay, last_time), 5)
    if varience:
        # print('\t\t', varience)
        tm = np.round(np.add(varience, delay), 5)
        # print('\t', tm)
    result = np.round(timeit.timeit(lambda: wait(tm), number=1), 5)
    # print(last_time)
    return result


def scan_adcs():
    """
    This will acquire the values for all of the ADC channels.
    """
    for adc in range(8):
        AnalogIn(mcp0, eval('MCP.P' + str(adc)))
        AnalogIn(mcp1, eval('MCP.P' + str(adc)))


def test_deg():
    """
    This tests with the servo controllers moving in degrees.
    """
    bw0.move_deg(0, 90)
    bw1.move_deg(0, 90)
    scan_adcs()


def test_raw():
    """
    This tests with the servo controllers moving in raw PWM.
    """
    bw0.move_deg(0, 127, raw=True)
    bw1.move_deg(0, 127, raw=True)
    scan_adcs()


def sweep_raw_single():
    """
    This will take our controller through one full motion sweep.
    """
    positions = np.array([0, 0, 0, 0, 0, 0, 0])
    rv = 2
    rg = int(180 / rv)
    print(rg)
    tm = lst = 0.0009
    while True:

        for inc in range(1, rg):
            positions = np.add(rv, positions).astype(int)
            # print(positions)
            try:
                bw0.moveall_deg(positions)
                bw1.moveall_deg(positions)
                scan_adcs()
                lst = time_offset(lst, tm)
            except ValueError:
                print(positions)
        bw0.configure()
        bw1.configure()
        rv = rv * -1


print('Single cycle Degrees:', timeit.timeit(lambda: test_deg(), number=1))
print('Single cycle raw:', timeit.timeit(lambda: test_raw(), number=1))

sweep_raw_single()
