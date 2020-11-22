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

*Flashing procedure*

1. disable spi overlays in config.txt and reboot.
2. run the flashit script.
3. short pads 2-3 (the ones without the thin solder strip).
4. whilst shorting the above pads, re-run the flashit script.
Results should indicate a successful flash.
Pin assignments can be altered in avrdude.conf
"""

import time
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
    post, pre = val >> 8, val & 255
    print('8bit split, low', bin(pre), hex(pre), 'high', bin(post), hex(post))


class BWServo:
    """
    This is the driver class for the BitWizard SPI servo controller SIP based on the ATTiny-44 processor.
    https://bitwizard.nl/wiki/Servo
    Note: We do not support software (bitbang) at this time.
    """

    def __init__(self, spi, cs, address=0x86, use_numpy=False, debug=False):
        """Initialize ATTiny-44 device with software SPI on the specified CLK,
        CS, and DO pins.  Alternatively can specify hardware SPI by sending an
        Adafruit_GPIO.SPI.SpiDev device in the spi parameter.

        NOTE: This only supports the SPI version of this module, I2C has proven to be far too slow for our application.

       :param spi: busio.SPI instance of the spi interface (sck/mosi, sck_1/mosi_1).
       :param cs: This is the chip select pin from digitalio: cs = digitalio.DigitalInOut(board.CE0).
       :param address: This is the assigned write address for the controller, defaults to 0x86
       :param use_numpy: This toggles numpy for the math functions.
       :param debug: Enables debugging messages.
       :type spi: busio.SPI
       :type cs: digitalio.DigitalInOut
       :type address: int
       :type use_numpy: bool
       :type debug: bool
        """
        self.debug = debug
        self._waddr = address
        self._raddr = address | 1
        self._np = use_numpy
        if self._np:
            import numpy as np
            self._np = np
        self._cs = cs
        self._spi = spi
        self._spi_dev = None
        self._read_buffer = bytearray(4)
        self._write_buffer = bytearray(4)
        self._pol = None
        self._hz = None
        self._ph = None
        self._bts = None

        self.configure()

    def configure(self, pol=0, phase=0, bits=8, hz=125000000):
        """
        This allows us to change the default chip configuration.

        :param pol: SPI bus polarity.
        :type pol: int
        :param phase: SPI bus phase.
        :type phase: int
        :param bits: SPI transaction bit length.
        :type bits: int
        :param hz: SPI baudrate.
        :type hz: int
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

    def dbg(self, value):
        """
        When debug is set to true this will return the various forms of bits, bytes and hex values being used.

        :param value: This is the value decoded and returned in the debug message.
        :type value: int, hex, bin
        """
        if self.debug:
            showbits(value)

    def _normalize(self):
        """
        This ensures our read and write buffers are the same size.
        """
        if len(self._write_buffer) > 4:
            self._write_buffer = self._write_buffer[:4]

    @staticmethod
    def _chkchan(channel):
        """
        This ensures our channel value is sane.

        :param channel: Value to confirm is within the range of channels.
        :type channel: int
        """
        if channel not in range(0, 6):
            raise ValueError

    @staticmethod
    def _chkdeg(degrees):
        """
        This checks to ensure our angle is sane.

        :param degrees: Value to confirm is within the range of motion (1-180).
        :type degrees: int
        """
        if degrees not in range(1, 180):
            raise ValueError

    @staticmethod
    def _splitbits(bits):
        """
        This takes a bit value longer than 8 and splits it in two

        :param bits: Value between 9 and 16 bits.
        :type bits: int, hex, bin
        :return: Tuple of 2 8bit values ordered with the lower bits first.
        :rtype: tuple
        """
        post, pre = int(bits >> 8), int(bits & 255)
        return pre, post

    @staticmethod
    def _mergebits(pre, post):
        """
        This takes two hex byte values and merges them into a 16bit value.

        :param pre: 8bit value of lower bits.
        :type pre: int, hex, bin
        :param post: 8bit value of higher bits.
        :type post: int, hex, bin
        :return: Integer value between 9 and 16 bits in length.
        :rtype: int
        """
        pre, post = bin(pre), bin(post)
        mg = eval(post + pre[2:])
        return mg

    def _convfromdeg(self, number):
        """
        This simply converts a number within 1-180 into a pwm value in 1-255.

        :param number: Value to be converted to PWM.
        :type number: int, hex, bin
        :return: PWM friendly integer.
        :rtype: int
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

        :param number: Value to be converted into degrees.
        :type number: int, hex, bin
        :return: Angular friendly integer.
        :rtype: int
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
        self._write_buffer[0] = self._waddr
        with self._spi_dev as spi:
            # pylint: disable=no-member
            spi.write(self._write_buffer)
        if self.debug:
            print('writebuffer', self._write_buffer)

    def _write_readinto(self):
        """
        This sends the write buffer to the slave and reads the response into the read_buffer.
        """
        self._normalize()
        with self._spi_dev as spi:
            # pylint: disable=no-member
            spi.write_readinto(self._write_buffer, self._read_buffer)
        if self.debug:
            print('writebuffer', self._write_buffer, 'readbuffer', self._read_buffer)

    def _write_reg(self, offset, register, value):
        """
        This performs a write operation on the specified register + offset.

        :param offset: Value to move from base register (register + offset).
        :type offset: int, hex, bin
        :param register: The base port register to operate on.
        :type register: int, hex, bin
        :param value: 1-16bit value to write into the target register.
        """
        self._normalize()
        if value > 65535:
            raise ValueError
        _reg = register | offset
        if self.debug:
            print('writing values', hex(self._write_buffer[0]), hex(_reg), hex(value))
        self._write_buffer[1] = _reg
        if value > 255:  # Handle 16 bit writes.
            self._write_buffer[2], self._write_buffer[3] = self._splitbits(value)
        else:
            self._write_buffer[2] = self._write_buffer[3] = value
        self._write()

    def _writemany_reg(self, register, values):
        """
        This will take a byte array of values, and write them to the specified register.

        :param register: The port register to operate on.
        :type register: int, hex, bin
        :param values: Array of values to be written to the target register.
        :type values: bytearray
        """
        self._write_buffer[1] = register
        self._write_buffer = self._write_buffer[:2] + values
        self._write()

    def _read_reg(self, offset, register):
        """
        This performs a read operation on the specified register + offset and populates the 4 byte read buffer.

        :param offset: Value to move from base register (register + offset).
        :type offset: int, hex, bin
        :param register: The port register to operate on.
        """
        self.configure(hz=25000)
        self._chkchan(offset)
        _reg = register | offset
        self._write_buffer[0] = self._raddr
        self._write_buffer[1] = _reg
        self._write_readinto()
        self.configure()

    def move_deg(self, channel, value):
        """
        This moves the target servo channel to the position of value in degrees (1-180).

        ;param channel: Servo channel (0-6) to operate on.
        :type channel: int, hex, bin
        :param value: Value to move the target server in degrees.
        :type value: int, hex, bin
        """
        self._write_reg(channel, 0x20, value)

    def moveall_deg(self, values):
        """
        This will take an array of values in degrees and pass them to all the channels in a single transaction.

        NOTE: This is only function in the custom firmware from BitWizard. and only functions with use_np set True.

        TODO: We really need to write a non-numpy method for this.

        :param values: Array of values in degrees to move servos.
        :type values: list
        """
        if self._np:
            values = self._np.array(values)
            values = bytearray(list(self._np.multiply(values, 1.415).astype(int)))
            self._writemany_reg(0x50, values)
        else:
            print('Aborted: this method requires numpy')

    def move_ms(self, channel, value):
        """
        This sets the target servo channel in microseconds (used for overdriving).

        :param channel: Servo channel (0-6) to operate on.
        :type channel: int, hex, bin
        :param value: Value to move the target server in microseconds.
        :type value: int, hex, bin
        """
        if value not in range(50, 2500):
            raise ValueError
        self._write_reg(channel, 0x28, value)

    def moveall_ms(self, values):
        """
        This takes a list of 16bit timing values (in microseconds) and moves all channels in a single transaction.
        :param values: Array of timings.
        :type values: list
        """
        vals = []  # type: list
        for value in values:
            vals += list(self._splitbits(value))
        self._writemany_reg(0x51, bytearray(vals))

    def get_deg(self, channel):
        """
        This reads the current position of a channel in degrees

        :param channel: This specifies the servo channel to read.
        :type channel: in, hex, bin
        :return: Servo position in degrees.
        :rtype: int
        """
        self._read_reg(channel, 0x20)
        answer = self._convfrompwm(self._read_buffer[2])
        return answer

    def get_ms(self, channel):
        """
        This reads back the timing value for the requested channel.

        :param channel: This specifies the servo channel to read.
        :type channel: in, hex, bin
        :return: Servo position in microseconds.
        :rtype: int
        """
        self._read_reg(channel, 0x20)
        answer = self._mergebits(self._read_buffer[2], self._read_buffer[3])
        return answer

    def set_timeout(self, channel, timeout):
        """
        This sets the timeout (return to nautral position) value for the specified channel in tenths of a second.

        :param channel: This specifies the servo channel.
        :type channel: in, hex, bin
        :param timeout: Servo timeout in tenths of a second.
        :type timeout: int, hex, bin
        """
        self._write_reg(channel, 0x38, timeout)

    def set_base_freq(self, value):
        """
        This lets us customize the base frequency of the PWM.

        :param value: 16bit value to set the base frequency in microseconds.
        :type value: int,, hex, bin
        """
        self._write_reg(0, 0x58, value)

    def set_base_multiplier(self, value):
        """
        This lets us customize the multiplier from the base frequency per-step in microseconds.

        base_frequency + multiplier * byte

        :param value: 8bit value in microseconds to step from the base frequency.
        :type value: int, hex, bin
        """
        self._write_reg(0, 0x59, value)

    def set_default(self, channel, value):
        """
        This sets the default position of a specific channel in degrees.

        :param channel: This specifies the servo channel.
        :type channel: in, hex, bin
        :param value: Default position in degrees.
        :type value: int, hex, bin
        """
        self._chkdeg(value)  # Ensure our position is sane.
        self._write_reg(channel, 0x30, self._convfrompwm(value))

    def change_address(self, address):
        """
        This changes the address of the slave.

        :param address: This specifies the new 8bit address that will be assigned to the module.
        :type address: int, hex, bin
        """
        wb = self._write_buffer
        registers = [
            (0xf1, 0x55),
            (0xf2, 0xaa),
            (address, 0x0)
        ]
        for register in registers:
            wb[1], wb[2] = register
            self._write()

    def test(self):
        """
        This will perform a test of the logic within this module.
        """
        print('beginning tests\n')
        time.sleep(1)

        print('\nidentifying board\n')
        self._read_reg(0, 0x01)
        print(self._read_buffer)

        print('\nservo 0 single sweep degrees\n')
        self.move_deg(0, 1)
        time.sleep(1)
        self.move_deg(0, 180)

        print('\nservo 0 read degrees\n')
        pos = self.get_deg(0)
        if pos != 180:
            print('read degrees test failed! value', pos, 'should be', 180)
        time.sleep(2)

        positions = [1, 1, 1, 1, 1, 1, 1]
        print('\nservo array sweep degrees\n')
        self.moveall_deg(positions)
        positions[0] = 180
        time.sleep(1)
        self.moveall_deg(positions)
        time.sleep(2)

        print('\nservo 0 single sweep microseconds\n')
        self.move_ms(0, 1000)
        time.sleep(1)
        self.move_ms(0, 2000)

        print('\nservo 0 read microseconds\n')
        pos = self.get_ms(0)
        if pos != 2000:
            print('read microseconds test failed! value', pos, 'should be', 2000)
        time.sleep(2)

        positions = [1000, 1000, 1000, 1000, 1000, 1000, 1000]
        print('\nservo array sweep microseconds\n')
        self.moveall_ms(positions)
        positions[0] = 2000
        time.sleep(1)
        self.moveall_ms(positions)

        print('movement tests complete')

