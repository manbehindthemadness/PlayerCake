"""
This is where we will hangle our servo control.
Note that we are gointo have to use numpy over the C api in order to get the reaction times we want.

https://circuitpython.readthedocs.io/projects/servokit/en/latest/api.html#implementation-notes

https://gis.stackexchange.com/questions/267084/tool-to-output-xy-from-an-input-xy-distant-and-angle

feedback servo https://www.adafruit.com/product/1404

i3c config https://www.raspberrypi.org/forums/viewtopic.php?t=34734

"""
from warehouse.math import TranslateCoordinates as Tc, raw_reverse as rr
from stage.oem.adafruit_servokit import ServoKit
import time


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
        self.l1 = self.tc(self.settings, 'LEG1', self.debug)
        self.l2 = self.tc(self.settings, 'LEG2', self.debug)
        self.l3 = self.tc(self.settings, 'LEG3', self.debug)
        self.l4 = self.tc(self.settings, 'LEG4', self.debug)
        self.legs = [self.l1, self.l2, self.l3, self.l4]
        self.refresh()

    def refresh(self):
        """
        This reloads our leg settings.
        """
        for leg in self.legs:
            leg.refresh()

    def jog(self, leg, axis):
        """
        This will jog an axis 5 times +- 10 degrees from neutral per cycle.
        """
        def mover():
            """
            This moves the servo.
            """
            for pm in rom:
                move_raw(self.controller, channel, pm, False)
                time.sleep(0.02)

        leg_settings = self.settings.legs[leg][axis]
        channel = leg_settings['pwm']
        neutral = leg_settings['nu']
        rom = list(range(neutral - 25, neutral + 25))
        # print('ROM', rom)
        count = 0
        while count < 5:
            print(count)
            mover()
            rom.reverse()
            mover()
            rom.reverse()
            count += 1


class Servos:
    """
    This is where we will send instructions directly to the PWM.
    """
    def __init__(self, controller):
        self.ready = True
        self.controller = controller
        self.settings = self.controller.settings
        self.rt_data = controller.rt_data
        self.settings = self.controller.settings
        self.servo_config = self.settings.pwm
        self.pwm = None
        self.last = dict()
        self.servos = None
        self.ready = False
        self.refresh()
        self.set()

    def refresh(self):
        """
        Reloads settings and environment
        """
        try:
            self.pwm = self.rt_data['PWM']['RAD']
            self.last = dict()
            self.servos = ServoKit(  # We need to take a deeper look into this...
                channels=16,
                reference_clock_speed=self.servo_config['clock'],
                frequency=self.servo_config['freq'],
                actuation_range=self.servo_config['range'],
                min_pulse=self.servo_config['pmin'],
                max_pulse=self.servo_config['pmax']
            )
            self.ready = True
            print('PWM Controller ready!')
        except KeyError:
            pass

    def set(self):
        """
        This takes the pwm values in the real time model and assigns them to the servo controller.

        TODO: We are going to need to add some conditions here for saftey.

        TODO: This is where acceleration and backlash are going to come into play, \
                In addition to biomemetic feedback constraints and gravitational offset.

        TODO: We really need to investigate where the slowdown is in this code. \
                It's messing with the servo test as well, and that worked great beforehand O_o...
        """
        freq = None
        if self.ready:  # Wait for the real time model to populate.
            try:
                for chan in self.pwm:
                    chan = str(chan)
                    # if chan not in self.last.keys():  # Set dummy last value.
                    #     self.last[chan] = -1
                    # lst_frq = self.last[chan]
                    freq = self.pwm[chan]
                    # if freq != lst_frq:  # Check to see if we have a new value.
                    if self.settings.pwm[chan]:  # Check for reversal.
                        freq = rr(freq, (0, 180))
                    self.servos.servo[int(chan)].angle = freq
                    self.last[chan] = freq  # Store last pwm value
            except ValueError as err:
                print(err)
                print('value:', freq)
        else:
            self.refresh()
            print('PWM waiting for real time model')


def move_raw(controller, channel, angle, relative=True):
    """
    This will move a servo from it's current position accounting for reverse settings.

    NOTE: This is a relative movement, when we say move 10, it will move 10 from the current position.

    NOTE: This does not take into account software minimum and maximum values as it's used to locate said values.

    'RAD': {   '0': 90,
              '1': 90,
              '10': 150,
              '12': 90,
              '13': 90,
              '14': 150,
              '2': 150,
              '4': 90,
              '5': 90,
              '6': 90,
              '8': 90,
              '9': 90
            },
    """
    rt_data = controller.rt_data
    channel = str(channel)
    pwm = rt_data['PWM']['RAD']
    if relative:
        if channel not in pwm.keys():  # Add channel to real time data model if missing.
            pwm[channel] = int(angle)
        else:
            current = pwm[channel]
            new_angle = current + angle
            if new_angle > 180:
                new_angle = 180
            elif new_angle < 0:
                new_angle = 0
            pwm[channel] = new_angle
    else:
        pwm[channel] = int(angle)
