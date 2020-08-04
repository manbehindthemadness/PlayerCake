"""
This is where we will store our I2C device code.
"""
import busio
import board


def i2cdetect():
    """
    Shows a list of irc devices on the controller bus.
    :return: Nothing
    """

    i2c = busio.I2C(board.SCL, board.SDA)
    print([hex(x) for x in i2c.scan()])