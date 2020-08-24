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
        self.imports = sys.modules.keys()
        self.exceptions = [
            'None',
        ]
        # print(self.imports)
        self.rt_self = rt_self
        self.settings = self.rt_self.settings
        self.command = ''
        self.output = None

    def verify(self):
        """
        This is used to detect dangerous or unauthorized commands.
        """
        valid = True
        command_digest = split_string(self.command)
        for digest in command_digest:
            if digest not in self.exceptions:
                for Import in self.imports:
                    for item in Import.split('.'):
                        if digest == item:
                            dprint(self.settings, ('Invalid command detected:', self.command, 'blocked by', Import))
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
            eval(self.command)
            dprint(self.settings, ('Command executed:', self.command,))

    def close(self):
        """
        This can be used to terminate the real time program.
        """
        self.rt_self.close()


def command_test():
    """
    Lets see if this shows up...
    """
    print('Test successful')
