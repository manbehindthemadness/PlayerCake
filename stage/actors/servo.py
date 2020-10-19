"""
This is where we will hangle our servo control.
Note that we are gointo have to use numpy over the C api in order to get the reaction times we want.

https://circuitpython.readthedocs.io/projects/servokit/en/latest/api.html#implementation-notes

https://gis.stackexchange.com/questions/267084/tool-to-output-xy-from-an-input-xy-distant-and-angle

feedback servo https://www.adafruit.com/product/1404

"""
from warehouse.math import TranslateCoordinates as Tc
from stage.oem.adafruit_servokit import ServoKit
# import numpy as np


class Legs:
    """
    This Inits our coordinate translation matrix and builds the local grids for the legs.

    This will update the real time data model's pwm values so the controller loop
        can assign it using the Servos class.
    """
    def __init__(self, controller, debug=False):
        self.controller = controller
        self.rt_data = self.controller.rt_data
        self.settings = self.controller.settings
        self.debug = debug
        self.tc = Tc
        self.dummy = None
        # TODO: Pack this into a loop so we can also populate the grid data into the real time model.
        self.l1 = self.tc(self.settings, 'LEG1', self.debug)
        self.l2 = self.tc(self.settings, 'LEG2', self.debug)
        self.l3 = self.tc(self.settings, 'LEG3', self.debug)
        self.l4 = self.tc(self.settings, 'LEG4', self.debug)
        self.legs = [self.l1, self.l2, self.l3, self.l4]

    def refresh(self):
        """
        This reloads our leg settings.
        """
        for leg in self.legs:
            leg.refresh()


class Servos:
    """
    This is where we will send instructions directly to the PWM.
    """
    def __init__(self, controller):
        self.controller = controller
        self.rt_data = controller.rt_data
        # self.temp = self.rt_data['temp']
        self.settings = self.controller.settings
        self.servo_config = self.settings.pwm
        self.pwm = self.rt_data['PWM']['RAD']
        self.servos = ServoKit(
            channels=16,
            reference_clock_speed=self.servo_config['clock'],
            frequency=self.servo_config['freq'],
            actuation_range=self.servo_config['range'],
            min_pulse=self.servo_config['pmin'],
            max_pulse=self.servo_config['pmax']
        )
        self.set()

    def set(self):
        """
        This takes the pwm values in the real time model and assigns them to the servo controller.

        TODO: We are going to need to add some conditions here for saftey.

        # TODO: This is where acceleration and backlash are going to come into play, \
                In addition to biomemetic feedback constraints and gravitational offset.
        """
        for chan in self.pwm:
            self.servos.servo[int(chan)].angle = self.pwm[chan]
