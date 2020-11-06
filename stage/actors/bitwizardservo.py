"""
This is our SPI driver for the bitwizard 7 channel SPI servo controller SIP.

https://wiki.python.org/moin/BitwiseOperators

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
"""
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI


channel_position_registers = [
    0x20,  # 32
    0x21,  # 33
    0x22,  # 34
    0x23,  # 35
    0x24,  # 36
    0x25,  # 37
    0x26,  # 38
]
channel_ms_registers = [
    0x28,  # 40
    0x29,  # 41
    0x2A,  # 42
    0x2B,  # 43
    0x2C,  # 44
    0x2D,  # 45
    0x2E,  # 46
]
channel_default_registers = [
    0x30,  # 48
    0x31,  # 49
    0x32,  # 50
    0x33,  # 51
    0x34,  # 52
    0x35,  # 53
    0x36,  # 54
]
channel_timeout_registers = [
    0x38,  # 56
    0x39,  # 57
    0x3A,  # 58
    0x3B,  # 59
    0x3C,  # 60
    0x3D,  # 61
    0x3E,  # 62
]
channel_global_register = 0x50  # 80
channel_read_register = 0x87  # 135
unlock_address_register = 0xF2  # 243
change_address_register = 0xF0  # 240
unclocking_register = 0xF1  # 241
identification_register = 0x01  # 1


class ATTiny44BW:
    """
    This is the driver class for the BitWizard SPI servo controller SIP based on the ATTiny-44 processor.
    """

    def __init__(self, clk=None, cs=None, miso=None, mosi=None, spi=None, gpio=None):
        """Initialize ATTiny-44 device with software SPI on the specified CLK,
        CS, and DO pins.  Alternatively can specify hardware SPI by sending an
        Adafruit_GPIO.SPI.SpiDev device in the spi parameter.

        NOTE: This only supports the SPI version of this module, I2C has proven to be far too slow for our application.
        """
        self._spi = None
        # Handle hardware SPI
        if spi is not None:
            self._spi = spi
        elif clk is not None and cs is not None and miso is not None and mosi is not None:
            # Default to platform GPIO if not provided.
            if gpio is None:
                gpio = GPIO.get_platform_gpio()
            self._spi = SPI.BitBang(gpio, clk, mosi, miso, cs)
        else:
            raise ValueError('Must specify either spi for for hardware SPI or clk, cs, miso, and mosi for softwrare SPI!')
        self._spi.set_clock_hz(1000000)
        self._spi.set_mode(0)
        self._spi.set_bit_order(SPI.MSBFIRST)
