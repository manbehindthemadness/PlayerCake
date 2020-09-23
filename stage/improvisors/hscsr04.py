"""
This is where we will store our echolocation code.
"""

import time
import RPi.GPIO as GPIO


class Sonar:
    """
    This is our echolocation class, currently using the hscsr04 module.
    """
    def __init__(self, controller):
        self.controller = controller
        self.rt_data = self.controller.rt_data
        self.trigger = None
        self.echo = None
        self.distance = None
        GPIO.setwarnings(False)
        # GPIO Mode (BOARD / BCM)
        GPIO.setmode(GPIO.BCM)

        self.GPIO_TRIGGER_right, self.GPIO_ECHO_right = self.controller.settings.r_echo

        GPIO.setup(self.GPIO_TRIGGER_right, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO_right, GPIO.IN)

        self.GPIO_TRIGGER_left, self.GPIO_ECHO_left = self.controller.settings.l_echo

        GPIO.setup(self.GPIO_TRIGGER_left, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO_left, GPIO.IN)

        self.GPIO_TRIGGER_rear, self.GPIO_ECHO_rear = self.controller.settings.b_echo

        GPIO.setup(self.GPIO_TRIGGER_rear, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO_rear, GPIO.IN)

        self.triggers = [
            self.GPIO_TRIGGER_right,
            self.GPIO_TRIGGER_left,
            self.GPIO_TRIGGER_rear
        ]
        self.echos = [
            self.GPIO_ECHO_right,
            self.GPIO_ECHO_left,
            self.GPIO_ECHO_rear
        ]
        self.names = [
            'right',
            'left',
            'rear'
        ]

    def ping(self):
        """
        This triggers a sonar ping.
        """
        for name, trig, ech in zip(self.names, self.triggers, self.echos):
            self.trigger = trig
            self.echo = ech
            self.get_distance()
            self.rt_data['sonar'][name] = self.distance
            print(name, self.distance)

    def get_distance(self):
        """
        This triggers a specific sonar module.
        """
        GPIO.output(self.trigger, True)

        time.sleep(0.00001)
        GPIO.output(self.trigger, False)

        StartTime = time.time()
        StopTime = time.time()

        timeout = 0.1
        timeout_start = time.time()
        while GPIO.input(self.echo) == 0 and time.time() < timeout_start + timeout:
            StartTime = time.time()

        while GPIO.input(self.echo) == 1 and time.time() < timeout_start + timeout:
            StopTime = time.time()

        TimeElapsed = StopTime - StartTime
        distance = (TimeElapsed * 34300) / 2
        if distance < 1:
            distance = 0
        self.distance = distance
