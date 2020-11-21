"""
This is our SPI driver for the bitwizard 7 channel SPI servo controller SIP.

* Author: Kevin Eales


**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases

** Notes and references:**

https://wiki.python.org/moin/BitwiseOperators

reference: https://readthedocs.org/projects/adafruit-circuitpython-busdevice/downloads/pdf/latest/

NOTE: Rememmber our binary operators.
        x << y
        Returns x with the bits shifted to the left by y places (and new bits on the right-hand-side are zeros). This is the same as multiplying x by 2**y.
        x >> y
        Returns x with the bits shifted to the right by y places. This is the same as //'ing x by 2**y.
        x & y
        Does a "bitwise and". Each bit of the output is 1 if the corresponding bit of x AND of y is 1, otherwise it's 0.
        x | y
        Does a "bitwise or". Each bit of the output is 0 if the corresponding bit of x AND of y is 0, otherwise it's 1.
        ~ x
        Returns the complement of x - the number you get by switching each 1 for a 0 and each 0 for a 1. This is the same as -x - 1.
        x ^ y
        Does a "bitwise exclusive or". Each bit of the output is the same as the corresponding bit in x if that bit in y is 0, and it's the complement of the bit in x if that bit in y is 1.

NOTE:
        Official "servo" standard says that servo signals are 1-2 ms long repeating at 20ms intervals (50 times per second).
        Now many servos will accept signals outside that range. Either by design or by accident. So most servos are built do turn about 180 degrees for the 1-2 ms signal range.
        But mechanically it is really easy to get about 270 degrees of rotation out of a servo. So many servo-manufacturers allow you to use say 0.75-2.25 range to address the whole
        270 degree range. The module uses its idea of a microsecond as a unit. So to be able to quickly (1 byte) specify a position,
        the units are 4 microsecond steps. I haven't looked closely at the code in a while but I'd expect that the pulses generated are 1000 microseconds + 4* the value you send.
        So in the longer pulses direction, you probably already have 20 microseconds of extra range. (1000+255*4 = 2020 microseconds).
        I think there are also 16-bit registers that allow you full access to the actual microseconds internal variable.
        About the "its idea of a microsecond": That's based on the internal 8MHz clock of the chip, That's an RC-oscillator,
        which could in theory vary by about 10%. In practice it is a lot more accurate.
        Keep in mind that the pulses are generated sequentially, The Tiny processor inside there is not well equipped to handle multiple signals accurately at the same time,
        but it can generate these sequential pulses very accurately. (About 125ns jitter IIRC).

NOTE: Speed change reference: https://www.raspberrypi.org/forums/viewtopic.php?t=177965

EXPERIMENT

import Adafruit_GPIO.SPI as SPI
spi = SPI.SpiDev(0, 0)
spi.set_clock_hz(200000)
spi.set_mode(0)
spi.set_bit_order(SPI.MSBFIRST)
"""

from adafruit_bus_device.spi_device import SPIDevice

__version__ = "0.1"


def showbits(val):
    """
    This will allow us to see the actual hex/binary representation of a value.

    This is more for cross checking things then anything else.
    """
    val = "{0:b}".format(val)
    print('raw ' + str(len(str(val))) + 'bit', val, hex(int(val)))
    val = int(val, 2)
    print('intconv', val, hex(int(val)))
    pre, post = val >> 8, val & 255
    print('8bit split, second', bin(pre), hex(pre), 'first', bin(post), hex(post))


class ATTiny44BW:
    """
    This is the driver class for the BitWizard SPI servo controller SIP based on the ATTiny-44 processor.

    Note: We do not support software (bitbang) at this time.
    """

    def __init__(self, spi, cs, address=0x86, use_numpy=False):
        """Initialize ATTiny-44 device with software SPI on the specified CLK,
        CS, and DO pins.  Alternatively can specify hardware SPI by sending an
        Adafruit_GPIO.SPI.SpiDev device in the spi parameter.

        NOTE: This only supports the SPI version of this module, I2C has proven to be far too slow for our application.

       :param spi: busio.SPI instance of the spi interface (sck/mosi, sck_1/mosi_1).
       :param cs: This is the chip select pin from digitalio: cs = digitalio.DigitalInOut(board.CE0).
       :param address: This is the assigned write address for the controller, defaults to 0x86
       :param use_numpy: This toggles numpy for the math functions.
       :type spi: busio.SPI
       :type cs: digitalio.DigitalInOut
       :type address: int
       :type use_numpy: bool
        """
        self._waddr = address
        self._raddr = address | 1
        self._np = use_numpy
        if self._np:
            import numpy as np
            self._np = np
        self._cs = cs
        self._spi = spi
        self._spi_dev = None
        self._bits = 8
        self._read_buffer = bytearray(4)
        self._read_buffer[0] = self._raddr
        self._write_buffer = bytearray(4)
        self._write_buffer[0] = self._waddr
        self._num_chans = 7
        self._pol = None
        self._hz = None
        self._ph = None
        self._bts = None

        self.configure()

    def configure(self, pol=0, phase=0, bits=8, hz=1000000):
        """
        This allows us to change the default chip configuration.
        """
        try:  # Lock the SPI bus and configure.
            while not self._spi.try_lock():
                pass
            self._pol = pol
            self._ph = phase
            self._bts = bits
            self._hz = hz
            self._spi.configure(
                baudrate=self._hz,
                polarity=self._pol,
                phase=self._ph,
                bits=self._bts
            )
            self._spi_dev = SPIDevice(self._spi, self._cs)
        finally:
            self._spi.unlock()

    def _normalize(self):
        """
        This ensures our read and write buffers are the same size.
        """
        if len(self._write_buffer) > 4:
            self._write_buffer = self._write_buffer[0:3]

    @staticmethod
    def _chkchan(channel):
        """
        This ensures our channel value is sane.
        """
        if channel not in range(0, 6):
            raise ValueError

    @staticmethod
    def _chkdeg(degrees):
        """
        This checks to ensure our angle is sane.
        """
        if degrees not in range(1, 180):
            raise ValueError

    @staticmethod
    def _splitbits(bits):
        """
        This takes a bit value longer than 8 and splits it in two
        """
        pre, post = hex(bits >> 8), hex(bits & 255)
        return pre, post

    @staticmethod
    def _mergebits(pre, post):
        """
        This takes two hex byte values and merges them into a 16bit value.
        """
        pre, post = bin(pre), bin(post)
        mg = eval(pre + post[2:])
        return mg

    def _convfromdeg(self, number):
        """
        This simply converts a number within 1-180 into a pwm value in 1-255.
        """
        if self._np:
            answer = self._np.multiply(number, 1.415)
        else:
            answer = number * 1.41
        if answer > 255:
            answer = 255
        return int(answer)

    def _convfrompwm(self, number):
        """
        This takes a pwm value in 1-255 and converts it into degrees 1-180.
        """
        if self._np:
            answer = self._np.divide(number, 1.415)
        else:
            answer = number / 1.41
        return int(answer)

    def _write(self):
        """
        Send write buffer to the slave.
        """
        with self._spi_dev as spi:
            # pylint: disable=no-member
            spi.write(self._write_buffer)

    def _write_readinto(self):
        """
        This sends the write buffer to the slave and reads the response into the read_buffer.
        """
        self._normalize()
        with self._spi_dev as spi:
            # pylint: disable=no-member
            spi.write_readinto(self._write_buffer, self._read_buffer)

    def move_deg(self, channel, value):
        """
        This moves the target servo channel to the position of value in degrees (1-180).
        """
        self._chkdeg(value)
        self._chkchan(channel)
        wb = self._write_buffer
        _chan = channel | 0x20
        _val = self._convfromdeg(value)
        wb[1] = _chan
        wb[2] = _val
        self._write()

    def move_array(self, values):
        """
        This will take an array of values in degrees and pass them to all the channels in a single transaction.

        NOTE: This is only function in the custom firmware from BitWizard. and only functions with use_np set True.
        """
        if self._np:
            values = self._np.array(values)
            values = bytearray(list(self._np.multiply(values, 1.415).round(0)))
            w_buf = bytearray([self._waddr, 0x50])
            w_buf += values
            self._write_buffer = w_buf
            self._write()
        else:
            print('Aborted: this method requires numpy')

    def move_ms(self, channel, value):
        """
        This sets the target servo channel in microseconds (used for overdriving).
        """
        if value not in range(50, 2500):
            raise ValueError
        self._chkchan(channel)
        wb = self._write_buffer
        _chan = channel | 0x28
        wb[1] = _chan
        wb[2], wb[3] = self._splitbits(value)
        self._write()

    def get_deg(self, channel):
        """
        This reads the current position of a channel in degrees
        """
        self._chkchan(channel)
        _chan = channel | 0x20
        self._write_buffer[1] = _chan
        self._write_readinto()
        answer = self._convfrompwm(self._read_buffer[2])
        return answer

    def get_ms(self, channel):
        """
        This reads back the timing value for the requested channel.
        """
        self._chkchan(channel)
        _chan = channel | 0x28
        self._write_buffer[1] = _chan
        self._write_readinto()
        answer = self._mergebits(self._read_buffer[2], self._read_buffer[3])
        return answer

    def set_timeout(self, channel, timeout):
        """
        This sets the timeout (return to nautral position) value for the specified channel in tenths of a second.
        """
        self._chkchan(channel)
        wb = self._write_buffer
        _chan = channel | 0x38
        wb[1] = _chan
        wb[2] = timeout
        self._write()

    def set_default(self, channel, value):
        """
        This sets the default position of a specific channel in degrees.
        """
        self._chkdeg(value)
        self._chkchan(channel)
        wb = self._write_buffer
        wb[2] = channel | 0x30
        wb[3] = self._convfromdeg(value)
        self._write()

    def change_address(self, address):
        """
        This changes the address of the slave.

        TODO: THis is untested and needs further validation that we won't brick the unit before being used.
        """
        wb = self._write_buffer
        wb[1], wb[2] = 0xf1, 0x55
        self._write()
        wb[1], wb[2] = 0xf2, 0xaa
        self._write()
        wb[1], wb[2] = address, 0x0
        self._write()
