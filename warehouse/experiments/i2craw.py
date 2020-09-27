"""
This is an interesting example of performing raw, unlimited i2c writes.

https://www.raspberrypi.org/forums/viewtopic.php?t=162248
"""
import fcntl
import io
import sys

# i2c_raw.py
# 2016-02-26
# Public Domain

I2C_SLAVE = 0x0703

if sys.hexversion < 0x03000000:
    def _b(x):
        return x
else:
    def _b(x):
        return x.encode('latin-1')


class i2c:

    def __init__(self, device, bus):

        self.fr = io.open("/dev/i2c-" + str(bus), "rb", buffering=0)
        self.fw = io.open("/dev/i2c-" + str(bus), "wb", buffering=0)

        # set device address

        fcntl.ioctl(self.fr, I2C_SLAVE, device)
        fcntl.ioctl(self.fw, I2C_SLAVE, device)

    def write(self, data):
        print(type(data))
        if type(data) is list:
            data = bytearray(data)
        elif type(data) is str:
            data = _b(data)
        self.fw.write(data)

    def read(self, count):
        return self.fr.read(count)

    def close(self):
        self.fw.close()
        self.fr.close()


if __name__ == "__main__":
    import i2c_raw

    dev = i2c_raw.i2c(0x32, 1)  # device 0x32, bus 1

    dev.write([10, 1, 2, 3, ord('B'), ord('E'), ord('E'), ord('F')])
    dev.write(b"\x0a\x01\x02\x03BEEF")
    dev.write("\x0a\x01\x02\x03BEEF")

    dev.close()
