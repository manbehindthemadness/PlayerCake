"""
This is where we will hangle our servo control.
Note that we are gointo have to use numpy over the C api in order to get the reaction times we want.

"""
# from adafruit_servokit import ServoKit
from warehouse.utils import iterate_to_dict
# import numpy as np


class InitAxis:
    """
    This holds our servo movement logic.

    TODO: DON'T forget to account for gravity offset!
    """
    def __init__(self, controller):
        self.controller = controller
        self.rt_data = self.controller.rt_data
        self.settings = self.controller.settings
        self.mover = self.rt_data['PWM']
        self.pwm_controller = None,
        self.pwm_channel = None
        self.axis_config = None
        self.positions = list()
        self.ax_max = None
        self.ax_min = None
        self.ax_neutral = None
        self.backlash = None
        self.max_speed = None
        self.acceleration = None  # Acceleration: TODO: Create definitions for these.
        self.position = None  # Radial position value
        self.position_coord = None  # XYZ positional coordinate.
        self.rad_scope = dict()  # This is the radial keyed scope of movement for this axis.
        self.pwm_scope = dict()  # This is the PWM keyed scope of movement for this axis.
        self.length = None  # This is the leg length
        self.range_of_motion_rad = None  # This is the overall possible range of radial values.
        self.rang_of_motion_pwm = None  # This is the trimmed overall range of PWM values.
        self.grid_coord = dict()  # This is our XYZ grid keyed with xyz coordinates.
        self.grid_pwm = dict()  # This is our XYZ grid keyed by PWM values.

    def figure_axis(self):
        """
        This figures out where we are on the radial axis translated to -min, zero, +max with respect to reversal

        NOTE: Zero point splits the positive and negative movement with respect to gravity neutral.

        NOTE: Basically we are taking min/max values of servo movement in relation to the grid and converting them to match the radial values of the controller

        NOTE: with respect to the trajectory spline axis neutral is evaluated at position X 0, Y 0, Z depends on configuration and footfall.
        """
        def find_trim(value):
            """
            This locates a trim offset by subtracting it's absolute value from 90
            """
            return 90 - abs(value)

        def trim_range(range_array, rmin, rmax):
            """
            This trims the range list removing the rmin and rmax from each end.
            """
            return range_array[find_trim(rmin), find_trim(rmax)]

        master_pwm_range = list(range(0, 180))
        master_range = list(range(-90, 90))  # Define maximum possible range of motion.
        self.range_of_motion_rad = trim_range(master_range, self.ax_min, self.ax_max)  # Define configured range of motion.
        self.rang_of_motion_pwm = trim_range(master_pwm_range, self.ax_min, self.ax_max)
        self.rad_scope = iterate_to_dict(self.range_of_motion_rad, self.rang_of_motion_pwm)
        self.pwm_scope = iterate_to_dict(self.rang_of_motion_pwm, self.range_of_motion_rad)

    def configure(self, axis, leg_id):
        """
        This resolves the settings and confiuration for a given PWM channel.
        """
        self.axis_config = self.settings.legs['LEG' + str(leg_id)][axis]
        self.length = self.settings.legs['LEG' + str(leg_id)]['len']
        self.pwm_channel = self.axis_config['pwm']
        self.pwm_controller = self.mover['RAD'][self.pwm_channel]
        self.ax_max = self.axis_config['max']
        self.ax_min = self.axis_config['min']
        self.ax_neutral = self.axis_config['nu']
        self.backlash = self.axis_config['bl']
        self.max_speed = self.axis_config['ms']
        self.acceleration = self.axis_config['ac']
        if isinstance(self.position, type(None)):  # set neutral position on init.
            self.position = 0

    def set_position_xyz(self):
        """
        This takes our position tuple and sends it to the PWM controller.
        """
