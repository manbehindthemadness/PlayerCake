# Copyright (c) 2020 Kevin Eales
# Author: Kevin Eales
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
SPI driver for the bitwizard 7 channel SPI servo controller SIP.

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases

** Notes and references:**

speed change: https://www.raspberrypi.org/forums/viewtopic.php?t=177965
module documentation: https://bitwizard.nl/wiki/Servo

** Example Usage: **

import busio
import board
import digitalio
from adafruit_bus_device.spi_device import SPIDevice
from bitwizardservo import BWServo


cs = digitalio.DigitalInOut(board.CE0)
spi_bus = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

srv = BWServo(spi_bus, cs)
srv.test()


### The below procedure only applies when writing a firmware revision and is kept only for reference ###

*Flashing procedure*

1. disable spi overlays in config.txt and reboot.
2. run the flashit script.
3. short pads 2-3 (the ones without the thin solder strip on the bottom of the board).
4. whilst shorting the above pads, re-run the flashit script (best to use a time delay script).
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

    NOTE: We do not support software (bitbang) at this time.

    NOTE: When reading the positional value of one of the servo channels it's expected for it to not be the exact value
            that was written. This is due to the positional value being clamped to an increment of the base multiplier
            plus the base frequency.
    """

    def __init__(self, spi, cs, address=0x86, use_numpy=False, debug=False):
        """Initialize ATTiny-44 device with software SPI on the specified CLK,
        CS, and DO pins.  Alternatively can specify hardware SPI by sending an
        Adafruit_GPIO.SPI.SpiDev device in the spi parameter.

        NOTE: This only supports the SPI version of this module, I2C has proven to be far too slow for our application.

       :param spi: busio.SPI instance of the spi interface (sck/mosi, sck_1/mosi_1).
       :param cs: This is the chip select pin from digitalio: cs = digitalio.DigitalInOut(board.CE0).
       :param address: This is the assigned write address for the controller, defaults to 0x86
       :param use_numpy: This toggles numpy for the math functions (much faster).
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
        self._ostart = 0
        self._oend = None
        self._istart = 0
        self._iend = None
        self._multi = 4
        self._freq = 988

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

    def _round_nearest(self, value, nearest):
        """
        This will round the value to the nearest increment.

        :param value: Number to be rounded.
        :type value: int
        :param nearest: The increment that we will round to.
        :type nearest: int
        :return: Value rounded to the nearest.
        :rtype: int
        """
        if self._np:
            answer = self._np.multiply(nearest, self._np.round(self._np.divide(value, nearest)))
        else:
            answer = nearest * round(value / value)
        return answer

    def _shiftread(self, size, skip=False):
        """
        This shifts the bits in the read buffer so we can clearly see our data.

        For 8bit values we shift the register by two.
        For 16bit reads we get the lowest bits in the third byte and the highest in the fourth, so we reverse and combine.

        :param size: Specifies the size of the read: 8 or 16 bits.
        :type size: int
        :param skip: Handy switch to bypass shifting opperations when needed.
        :type skip: bool
        :return: Normalized byte value.
        :rtype: int
        """
        rb = self._read_buffer
        if not skip:
            if size == 8:
                sb = self._read_buffer[2] << 0x2
            elif size == 16:
                sb = self._mergebits(rb[2], rb[3])
            else:
                sb = rb
            if self.debug:
                print('shifting bits for size', size, 'result', sb)
        else:
            sb = rb[2]
        return sb

    def _normalize(self, length=4):
        """
        This ensures our read and write buffers are the same size.

        :param length: Resize the read and write buffers length.
        :type length: int
        """
        self._write_buffer = self._write_buffer[:2]
        self._write_buffer += bytearray(length - 2)
        self._read_buffer = bytearray(length)

    def _chkchan(self, channel):
        """
        This ensures our channel value is sane.

        NOTE: This is a debug function only.

        :param channel: Value to confirm is within the range of channels.
        :type channel: int
        """
        if channel not in range(0, 6) and self.debug:
            raise ValueError

    def _chkdeg(self, degrees):
        """
        This checks to ensure our angle is sane.

        NOTE: This is a debug function only.

        :param degrees: Value to confirm is within the range of motion (1-180).
        :type degrees: int
        """
        if degrees not in range(1, 180) and self.debug:
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
        Send write buffer.
        """
        self._write_buffer[0] = self._waddr
        with self._spi_dev as spi:
            # pylint: disable=no-member
            spi.write(
                self._write_buffer,
                self._ostart,
                self._oend
            )
        if self.debug:
            print('writebuffer', self._write_buffer)

    def _write_readinto(self, length=5):
        """
        This sends the write buffer to the slave and reads the response into the read_buffer.

        :param length: This can be used to adjust the read buffer length.
        :type length: int
        """
        self.configure(hz=50000)
        self._normalize(length)
        with self._spi_dev as spi:
            # pylint: disable=no-member
            spi.write_readinto(
                self._write_buffer,
                self._read_buffer,
                self._ostart,
                self._oend,
                self._istart,
                self._iend
            )
        if self.debug:
            print('writebuffer', self._write_buffer, 'readbuffer', self._read_buffer)
        self.configure()

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

    def _read_reg(self, offset, register, length=5):
        """
        This performs a read operation on the specified register + offset and populates the 4 byte read buffer.

        :param offset: Value to move from base register (register + offset).
        :type offset: int, hex, bin
        :param register: The port register to operate on.
        :type register: int, hex, bin
        :param length: This can be used to adjust the read buffer length.
        :type length: int
        """

        self._chkchan(offset)
        _reg = register | offset
        self._write_buffer[0] = self._raddr
        self._write_buffer[1] = _reg
        self._write_readinto(length)

    def move_deg(self, channel, value, raw=False):
        """
        This moves the target servo channel to the position of value in degrees (1-180).

        ;param channel: Servo channel (0-6) to operate on.
        :type channel: int, hex, bin
        :param value: Value to move the target server in degrees.
        :type value: int, hex, bin
        :param raw: This is just for testing the raw pwm values.
        :type raw: bool
        """
        if not raw:
            value = self._convfromdeg(value)
        self._write_reg(channel, 0x20, value)

    def moveall_deg(self, values, raw=False):
        """
        This will take an array of values in degrees and pass them to all the channels in a single transaction.

        NOTE: This is only function in the custom firmware from BitWizard. and only functions with use_np set True.

        :param values: Array of values in degrees to move servos.
        :type values: list
        :param raw: When set to True we will write in PWM values from 1-255.
        :type raw: bool
        """
        if not raw:
            if self._np:
                values = self._np.array(values)
                values = list(self._np.multiply(values, 1.415).astype(int))
            else:
                for idx, value in enumerate(values):
                    values[idx] = int(value * 1.4)
        self._writemany_reg(0x50, bytearray(values))

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

    def get_deg(self, channel, raw=False):
        """
        This reads the current position of a channel in degrees

        :param channel: This specifies the servo channel to read.
        :type channel: int, hex, bin
        :param raw: When set to True we will read in PWM values from 1-255.
        :type raw: bool
        :return: Servo position in degrees.
        :rtype: int
        """
        self._read_reg(channel, 0x20)
        answer = self._shiftread(8)
        if not raw:
            answer = self._convfrompwm(answer)
        if not answer:
            answer = 1
        return answer

    def get_ms(self, channel):
        """
        This reads back the timing value for the requested channel.

        :param channel: This specifies the servo channel to read.
        :type channel: int, hex, bin
        :return: Servo position in microseconds.
        :rtype: int
        """
        self._read_reg(channel, 0x28)
        answer = self._shiftread(16)
        return answer

    def get_timeout(self, channel):
        """
        This reads back the timeout value for the requested channel (time inactive before it reverts to default position).

        :param channel: This specifies the servo channel to read.
        :type channel: int, hex, bin
        :return: Servo position in microseconds.
        :rtype: int
        """
        self._read_reg(channel, 0x38)
        answer = self._shiftread(8, skip=True)
        return answer

    def get_default(self, channel):
        """
        This reads back the neutral (default) position a servo will move to during power on or after a timeout.

        :param channel: This specifies the servo channel to read.
        :type channel: int, hex, bin
        :return: Servo default in microseconds.
        :rtype: int
        """
        self._read_reg(channel, 0x30)
        answer = self._shiftread(8, skip=True)
        return answer

    def set_timeout(self, channel, timeout):
        """
        This sets the timeout (return to nautral position) value for the specified channel in tenths of a second.

        :param channel: This specifies the servo channel.
        :type channel: int, hex, bin
        :param timeout: Servo timeout in tenths of a second.
        :type timeout: int, hex, bin
        """
        self._write_reg(channel, 0x38, timeout)

    def set_base_freq(self, value):
        """
        This lets us customize the base frequency of the PWM.

        :param value: 16bit value to set the base frequency in microseconds.
        :type value: int, hex, bin
        """
        self._freq = value
        self._write_reg(0, 0x58, value)

    def set_base_multiplier(self, value):
        """
        This lets us customize the multiplier from the base frequency per-step in microseconds.

        base_frequency + multiplier * byte

        :param value: 8bit value in microseconds to step from the base frequency.
        :type value: int, hex, bin
        """
        self._multi = value
        self._write_reg(0, 0x59, value)

    def set_default(self, channel, value, raw=False):
        """
        This sets the default position of a specific channel in degrees.

        :param channel: This specifies the servo channel.
        :type channel: int, hex, bin
        :param value: Default position in degrees.
        :type value: int, hex, bin
        :param raw: When set to True we will write in PWM values from 1-255.
        :type raw: bool
        """
        self._chkdeg(value)  # Ensure our position is sane.
        if not raw:
            value = self._convfrompwm(value)
        self._write_reg(channel, 0x30, value)

    def change_address(self, address):
        """
        This changes the address of the slave.

        NOTE: Addresses are handled in bytes with the lowest bit set to zero. The 7 higher bits represent the address
                whilst the lowest bit signals read (high) or write (low). An example of this from the defaults can be
                seen here:
                address = 0x86 10000110 (write)
                          0x87 10000111 (read)

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

    def identify(self):
        """
        This reads back the neutral (default) position a servo will move to during power on or after a timeout.

        :return: Board identification.
        :rtype: bytestring
        """
        self._read_reg(0, 0x01, length=15)
        answer = self._shiftread(15)
        return answer[2:]

    def test(self):
        """
        This will perform a test of the logic within this module.

        NOTE: When doing read operations it's important to keep in mind that the position read will not always
                be the position written. This is bacause we are clamped to increments of the
                base multiplier (default 4) from the base frequency (default 988).
        """
        def fail(value, expected_value, fail_message):
            """
            This just confirms a value meets the expected value, if not iw will print the fail_message and return False.
            """
            result = True
            if value != expected_value:
                print(*fail_message)
                result = False
            return result

        success = []

        print('beginning tests\n')
        time.sleep(1)
        print('identifying board\n')
        ident = self.identify()
        print(ident.decode())
        success.append(fail(ident.decode()[:9], 'spi_servo', ('failed to identify board!',)))
        print('reading config:\n')
        print('channel 0 timeout:', self.get_timeout(0))
        print('channel 0 default:', self.get_default(0))

        print('servo 0 single sweep degrees\n')
        self.move_deg(0, 1)
        time.sleep(1)
        self.move_deg(0, 180)

        print('servo 0 read degrees\n')
        pos = self.get_deg(0)

        success.append(fail(pos, 178, ('read degrees test failed! value:', pos, 'should be:', 178)))
        time.sleep(1)

        self.move_deg(0, 252, raw=True)
        lpos = self.get_deg(0, raw=True)
        print('low position:', lpos)
        print('expected value: 252\n')
        success.append(fail(lpos, 252, ('failure!',)))

        positions = [1, 1, 1, 1, 1, 1, 1]
        print('servo array sweep degrees\n')
        self.moveall_deg(positions)
        positions[0] = 180
        time.sleep(1)
        self.moveall_deg(positions)
        time.sleep(1)

        print('servo 0 single sweep microseconds\n')
        self.move_ms(0, 1000)
        time.sleep(1)
        self.move_ms(0, 2000)

        print('servo 0 read microseconds\n')
        pos = self.get_ms(0)
        success.append(fail(pos, 2000, ('read microseconds test failed! value:', pos, 'should be:', 2000)))
        time.sleep(1)

        self.move_ms(0, 988)
        lpos = self.get_ms(0)
        print('low position:', lpos)
        print('expected value: 988\n')
        success.append(fail(lpos, 988, ('Failure!',)))

        positions = [1000, 1000, 1000, 1000, 1000, 1000, 1000]
        print('servo array sweep microseconds\n')
        self.moveall_ms(positions)
        positions[0] = 2000
        time.sleep(1)
        self.moveall_ms(positions)
        time.sleep(1)

        print('changing frequency and multiplier to 700-2485, 7\n')
        self.set_base_freq(700)
        self.set_base_multiplier(7)

        print('servo 0 single sweep pwm\n')
        self.move_deg(0, 1, raw=True)
        time.sleep(1)
        self.move_deg(0, 255, raw=True)
        time.sleep(1)

        print('setting channel 0 default to 90 degrees')
        self.set_default(0, 255, raw=True)
        print('setting channel 0 timeout to 1 second')
        self.set_timeout(0, 20)
        print('reading back values')
        tmot = self.get_timeout(0)
        print('channel 0 timeout:', tmot)
        success.append(fail(tmot, 20, ('set timeout failure!',)))

        deft = self.get_default(0)
        print('channel 0 default:', deft)
        success.append(fail(deft, 255, ('set default failure!',)))

        time.sleep(3)
        dg, ms = self.get_deg(0), self.get_ms(0)
        print('timeout position custom freq:', dg, ms, '\n')
        fail(dg, 180, ('warning: read pwm value not updated after timeout',))
        success.append((ms, 2485, ('timeout movement failure!',)))

        print('reverting base values\n')
        self.set_base_freq(988)
        self.set_base_multiplier(4)

        self.move_deg(0, 1, raw=True)
        time.sleep(3)
        dg, ms = self.get_deg(0), self.get_ms(0)
        print('timeout position default freq:', dg, ms, '\n')
        fail(dg, 180, ('warning: read pwm value not updated after timeout',))
        success.append((ms, 2485, ('timeout movement failure!',)))

        if False not in success:
            print('\nself-test passed!\n')
        else:
            print('\nself-test failed!\n')
