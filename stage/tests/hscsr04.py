"""
This is a file to test the HC-SR04 echolocation sensor.
"""
import time

# Libraries
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
# GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

# set GPIO Pins Right sensor
GPIO_TRIGGER_right = 27
GPIO_ECHO_right = 22

# set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER_right, GPIO.OUT)
GPIO.setup(GPIO_ECHO_right, GPIO.IN)

# set GPIO Pins Left sensor
GPIO_TRIGGER_left = 23
GPIO_ECHO_left = 24

# set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER_left, GPIO.OUT)
GPIO.setup(GPIO_ECHO_left, GPIO.IN)

# set GPIO Pins rear sensor
GPIO_TRIGGER_rear = 25
GPIO_ECHO_rear = 9

# set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER_rear, GPIO.OUT)
GPIO.setup(GPIO_ECHO_rear, GPIO.IN)


def distance(trigger, echo):
    """
    Lets get a distance form these sensors!
    :param trigger:
    :param echo:
    :return:
    """
    # set Trigger to HIGH
    GPIO.output(trigger, True)

    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(trigger, False)

    StartTime = time.time()
    StopTime = time.time()

    # save StartTime
    timeout = 0.1
    timeout_start = time.time()
    while GPIO.input(echo) == 0 and time.time() < timeout_start + timeout:
        StartTime = time.time()

    # save time of arrival
    while GPIO.input(echo) == 1 and time.time() < timeout_start + timeout:
        StopTime = time.time()

    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance_ = (TimeElapsed * 34300) / 2

    return distance_


print('starting')
if __name__ == '__main__':
    try:
        while True:
            message = "Distance right = %.1f cm" % distance(GPIO_TRIGGER_right, GPIO_ECHO_right)
            time.sleep(0.1)
            message = message + " Distance left = %.1f cm" % distance(GPIO_TRIGGER_left, GPIO_ECHO_left)
            time.sleep(0.1)
            message = message + " Distance rear = %.1f cm" % distance(GPIO_TRIGGER_rear, GPIO_ECHO_rear)
            print(message)
            time.sleep(0.25)
            # TODO: This need to have a rational tolerance regulator, as the results are only partially accurate.

        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
