"""
Example of a cooling system loop.

"""
# import RPi.GPIO as IO
# IO.setwarnings(False)
# IO.setmode (IO.BCM)
# IO.setup(12,IO.OUT)
# p = IO.PWM(12, 255)
# p.start(100.0)

# import RPi.GPIO as GPIO
# GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(12, GPIO.OUT)
# led_pwm = GPIO.PWM(12, 100)
# led_pwm.start(0)

import RPi.GPIO as GPIO
import time
from subprocess import PIPE, Popen


def get_cpu_temperature():
    """get cpu temperature using vcgencmd"""
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    output = output.decode("utf8")
    return float(output[output.index('=') + 1:output.rindex("'")])


# print(get_cpu_temperature())
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)
GPIO.output(12, 0)
while True:
    temp = get_cpu_temperature()
    print(temp)
    if temp > 35.0:
        print('cooling on')
        GPIO.output(12, 1)
        for inc in range(0, 10):
            print(get_cpu_temperature())
            time.sleep(1)
    else:
        print('cooling off')
        GPIO.output(12, 0)
    time.sleep(1)

# GPIO.output(12, 1)
# time.sleep(5)
# GPIO.output(12, 0)
