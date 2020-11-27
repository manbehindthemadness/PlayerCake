"""Simple test for a standard servo"""
# import time
import busio
import board
import digitalio
from adafruit_bus_device.spi_device import SPIDevice


cs = digitalio.DigitalInOut(board.CE0)
spi_bus = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
while not spi_bus.try_lock():
    pass
spi_bus.configure(baudrate=125000000)
spi_bus.unlock()
spi_dev = SPIDevice(spi_bus, cs)

cs1 = digitalio.DigitalInOut(board.CE1)
spi_bus1 = busio.SPI(clock=board.SCK_1, MISO=board.MISO_1, MOSI=board.MOSI_1)
while not spi_bus1.try_lock():
    pass
spi_bus1.configure(baudrate=125000000)
spi_bus1.unlock()
spi_dev1 = SPIDevice(spi_bus1, cs1)


def cycle_test():
    """
    This performs a full range of motion sweep across all channels.
    """

    def write(buf, spi_device):
        """
        Write to device
        """
        with spi_device as spi:
            # pylint: disable=no-member
            spi.write(buf)
            # time.sleep(0.01)

    def cycle(buf, spi_device, values):
        """
        This cycles through an array of values.
        """
        for value in values:
            for chan in range(2, 9):
                buf[chan] = value
            write(buf, spi_device)
            # time.sleep(0.02)

    out_buf = bytearray(9)
    for pos in out_buf:  # Set to neutral.
        out_buf[pos] = 0x7f

    print(out_buf)

    out_buf[0] = 0x86  # Slave address.
    out_buf[1] = 0x50  # Port register.

    incr = list()
    for inc in range(1, 180):
        incr.append(int(inc * 1.41))
    increments = [x for x in incr if x % 1 == 0]
    print(increments)

    while True:
        cycle(out_buf, spi_dev, increments)
        cycle(out_buf, spi_dev1, increments)
        increments.reverse()


def identify():
    """
    This is a read tester
    """
    def _shiftread(size):
        """
        This shifts the bits in the read buffer so we can clearly see our data.
        """
        sb = None
        if size == 8:
            rb = in_buf
            sb = rb[2] + rb[3]
        elif size == 16:
            rb = in_buf
            a, b = bin(rb[3]), bin(rb[2])
            sb = eval(a + b[2:])
        return sb

    out_buf = in_buf = bytearray(32)
    out_buf[0] = 0x87  # Slave address.
    out_buf[1] = 0x20  # Port register.
    with spi_dev as spi:
        # pylint: disable=no-member
        # spi.readinto(in_buf, start=0x20, write_value=0x87)
        spi.write_readinto(out_buf, in_buf)
        # time.sleep(0.01)
    print(in_buf)
    print(_shiftread(16))
