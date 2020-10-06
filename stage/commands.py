"""
There is where we will add command execution logic.

NOTE: We will evaluate the imports to a list so we can cross check the ingress and prevent hostile code injection.
        This *should* allow for a great deal of flexibility whilst remaining perfectly "safe".
"""

import sys
import time
from warehouse.system import system_command
from warehouse.utils import split_string
from warehouse.loggers import dprint


class Command:
    """
    This is the command parser we will use to
    """
    def __init__(self, rt_self):
        """
        :param rt_self: Pass the real time program here.
        :type rt_self: stage.rt.Start
        """
        self.imports = list(sys.modules.keys())
        self.imports.append('import')  # Prevent commands from importing modules (for saftey).
        self.rt_self = rt_self
        self.settings = self.rt_self.settings
        self.exceptions = self.settings.command_exceptions
        self.lines = self.rt_self.lines
        self.command = ''
        self.output = None
        self.whitelist = [
            'debug_mode("adc")',
            'send_settings()',
            'settings_save()'
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
        if self.command not in self.whitelist:
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
            except TypeError as err:
                print('exec + ', self.command, err)
        # self.command = ''

    def close(self):
        """
        This can be used to terminate the real time program.
        """
        self.rt_self.close()

    def debug_mode(self, mode, skip=False):
        """
        Here we will change our screen debugging mode.
        """
        self.rt_self.settings.debug_screen_mode = mode
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
        self.rt_self.netcom.reconnect()

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
            self.dummy = setting
            exec('self.settings.' + self.dummy + ' = 0')
            self.settings.save()

    def reset_gyro(self):
        """
        This resets the calibrations of the BNO055 9DOF.
        """
        self.rt_self.dof.reset_calibration()

    def send_settings(self):
        """
        This will transmit our settings to director.
        """
        print('sending settings', self.settings.settings['debug_screen_mode'])
        self.rt_self.send({'SENDER': self.settings.stage_id, 'DATA': {'SETTINGS': self.settings.settings}})

    def send_stream(self, requested_data, requested_cycletime, mode=None):
        """
        This will initiate a datastream to the director.

        NOTE: Requested data represents the key in the stages realtime model that will be transmitted.
        """
        if mode:
            self.debug_mode(mode, True)
            time.sleep(1)
        self.rt_self.send_datastream(requested_data, requested_cycletime)

    def close_stream(self):
        """
        This will close an outgoing datastream.
        """
        self.rt_self.datastream_term = True


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
