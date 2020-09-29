"""
There is where we will add command execution logic.

NOTE: We will evaluate the imports to a list so we can cross check the ingress and prevent hostile code injection.
        This *should* allow for a great deal of flexibility whilst remaining perfectly "safe".
"""

import sys
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

    def verify(self):
        """
        This is used to detect dangerous or unauthorized commands.
        """
        valid = True
        self.lines.append('CMD:' + self.command)
        command_digest = split_string(self.command)
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
        if valid:
            try:
                exec(self.command)
            except NameError:
                exec('self.' + self.command)
            dprint(self.settings, ('Command executed:', self.command,))

    def close(self):
        """
        This can be used to terminate the real time program.
        """
        self.rt_self.close()

    def debug_mode(self, mode):
        """
        Here we will change our screen debugging mode.
        """
        self.rt_self.settings.debug_screen_mode = mode
        # print(self.rt_self.settings.debug_screen_mode)


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
