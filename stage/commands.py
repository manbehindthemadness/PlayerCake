"""
There is where we will add command execution logic.

NOTE: We will evaluate the imports to a list so we can cross check the ingress and prevent hostile code injection.
        This *should* allow for a great deal of flexibility whilst remaining perfectly "safe".
"""

import sys
import time
import traceback
from warehouse.system import system_command
from warehouse.utils import split_string
from warehouse.loggers import dprint
from stage.actors.servo import move_raw


class Command:
    """
    This is the command parser we will use to
    """
    def __init__(self, controller):
        """
        :param controller: Pass the real time program here.
        :type controller: stage.rt.Start
        """
        self.imports = list(sys.modules.keys())
        self.imports.append('import')  # Prevent commands from importing modules (for saftey).
        self.controller = controller
        self.rt_data = self.controller.rt_data
        self.settings = self.controller.settings
        self.grids = self.controller.grids
        self.exceptions = self.settings.command_exceptions
        self.lines = self.controller.lines
        self.command = ''
        self.output = None
        self.whitelist = [
            'debug_mode',
            'send_settings',
            'settings_save',
            'send_stream',
            'servo',
            'jog_servo',
            'reverse_axis',
            'lock_limit',
            'channel_map',
            'train_axis',

        ]
        self.dummy = None

    def verify(self):
        """
        This is used to detect dangerous or unauthorized commands.
        """
        valid = True
        self.lines.append('CMD:' + self.command)
        print(self.command)
        command_digest = split_string(self.command)
        cmd = self.command.split('(')[0]
        if cmd not in self.whitelist:
            for digest in command_digest:
                if digest not in self.exceptions:
                    for Import in self.imports:
                        for item in Import.split('.'):
                            if digest == item:
                                dprint(self.settings, ('Invalid command detected:', self.command, 'blocked by', Import))
                                self.lines.append('CMD: invalid')
                                self.lines.append('CMD: aborting')
                                valid = False
        return valid

    def execute(self, command):
        """
        This performs the execution of the supplied command.

        :param command: String form of command to be executed.
        :type command: str
        :rtype: exec
        """
        self.command = command
        valid = self.verify()
        if valid and command:
            try:
                try:
                    exec(self.command)
                except NameError:
                    exec('self.' + self.command)
                dprint(self.settings, ('Command executed:', self.command,))
            except (TypeError, NameError) as err:
                print('exec + ', self.command, err)
                traceback.print_exc()

    def close(self):
        """
        This can be used to terminate the real time program.
        """
        self.controller.close()

    def debug_mode(self, mode, skip=False):
        """
        Here we will change our screen debugging mode.
        """
        self.controller.settings.debug_screen_mode = mode
        self.setting_change('debug_screen_mode', mode)
        if skip:
            self.settings.save()

    def setting_change(self, setting, value):
        """
        This makes a change to our real time settings.
        """
        print('updating setting', setting, value)
        self.settings.set(setting, value)
        self.settings.save()

    def settings_save(self):
        """
        Saves the running settings to file.
        """
        # print(self.rt_self.rt_data['LISTENER'])

        self.settings.save()

    def network_reset(self):
        """
        This triggers a network reset of the stage instance.
        """
        self.controller.netcom.reconnect()

    def reset_imu(self):
        """
        This resets the IMU calibrations.
        """
        for setting in [
            'magxmin',
            'magxmax',
            'magymin',
            'magymax',
            'magzmin',
            'magzmax'
        ]:
            exec('self.settings.' + setting + ' = 0')
            print('self.settings.' + setting + ' = 0')
        self.settings.save()

    def reset_gyro(self):
        """
        This resets the calibrations of the BNO055 9DOF.
        """
        self.controller.dof.reset_calibration()

    def send_settings(self):
        """
        This will transmit our settings to director.
        """
        print('sending settings', self.settings.settings['debug_screen_mode'])
        self.controller.send({'SENDER': self.settings.stage_id, 'DATA': {'SETTINGS': self.settings.settings}})

    def send_stream(self, requested_data, requested_cycletime, mode=None):
        """
        This will initiate a datastream to the director.

        NOTE: Requested data represents the key in the stages realtime model that will be transmitted.
        """
        if mode:
            self.debug_mode(mode, True)
            time.sleep(1)
        self.controller.send_datastream(requested_data, requested_cycletime)

    def close_stream(self):
        """
        This will close an outgoing datastream.
        """
        self.controller.datastream_term = True

    def servo(self, channel, angle):
        """
        This will move a servo from it's current position accounting for reverse settings.

        NOTE: This is a relative movement, when we say move 10, it will move 10 from the current position.
        """
        move_raw(self.controller, channel, angle)

    def jog_servo(self, leg, axis):
        """
        This will jog a servo on the specified leg and axis.
        """
        self.controller.legs.jog(leg, axis)

    def reverse_axis(self, channel):
        """
        This will reverse the direction of a servo on the specified channel.
        """
        value = False
        pwm_settings = self.settings.pwm
        pwm_val = pwm_settings[channel]
        if not pwm_val:
            value = True
        pwm_settings[channel] = value
        self.setting_change('pwm', pwm_settings)

    def lock_limit(self, leg_id, name, axis):
        """
        This will set the axis limit on a specific leg by axis by name.
        """
        channel = str(self.settings.legs[leg_id][axis]['pwm'])
        pwm_val = self.controller.rt_data['PWM']['RAD'][channel]
        print(pwm_val, channel)
        legs = self.settings.legs
        legs[leg_id][axis][name] = pwm_val
        self.settings.set('legs', legs)

    def channel_map(self, leg_id, axis, name, value):
        """
        This will allow us to change the PWM and ADC channel mappings for a target leg by axis.
        """
        legs = self.settings.legs
        legs[leg_id][axis][name] = int(value)
        self.settings.set('legs', legs)

    def train_axis(self, leg_id, axis):
        """
        This will record the adc values on a specific leg axis and add the mappings into the grids.ini file.
        """
        ax = self.settings.legs[leg_id][axis]  # Fetch axis info.

        rom = list(range(ax['min'], ax['max']))  # Get range of motion.
        fb = self.grids.feedback  # Fetch feedback mappings.
        mapp = {
            'p2a': dict(),
            'a2p': dict(),
        }
        # TODO: We need to stick this into a function as we need to run at least once in each direction.
        for angle in rom:
            self.controller.rt_data['PWM']['RAD'][str(ax['pwm'])] = angle  # Set axis position.
            mapping = mapp['p2a'][str(angle)] = list()
            repeat = 0
            while repeat < 5:
                # TODO: We are clamping this value to two digits... This might need to be a configurable settings in the future.
                adc = self.controller.rt_data['ADC'][str(ax['adc'])]  # Fetch ADC input.
                if adc not in mapping:
                    print(angle, adc)
                    mapping.append(adc)
                time.sleep(0.1)  # Wait a moment to sample variations.
                repeat += 1
        fb[str(ax['adc'])] = mapp
        self.grids.set('feedback', fb)
        self.grids.save()


def command_test():
    """
    Lets see if this shows up...
    """
    print('Test successful')


def reboot():
    """
    Reboots the SOC.
    """
    system_command(['reboot'])


def poweroff():
    """
    Shuts down the SOC.
    """
    system_command(['poweroff'])


def selftest():
    """
    Performs hardware self-test.
    """
    print('selftest logic here')


def calibrate_safe():
    """
    Performs a calibration that's safe to use when the unit is standing on the ground.
    """
    print('safe calibration logic here')


def calibrate():
    """
    Performs a full calibration assuming the unit isn't touching the ground.
    """
    print('full calibration logic here')


def report():
    """
    This causes the unit to upload it's virtual telemetry to the director.
    """
    print('report logic here')


def recall():
    """
    This is used to instruct the unit to move back to it's starting position.
    """
    print('recall logic here')


def shelter():
    """
    This causes the unit to assume a defensive position to prevent damage.
    """
    print('shelter logic here')
