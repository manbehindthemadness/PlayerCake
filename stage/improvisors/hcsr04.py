"""
This is where we will store our echolocation code.
"""

import time
import board
import adafruit_hcsr04


class Sonar:
    """
    his is our echolocation class, currently using the hcsr-04 module.
    """
    def __init__(self, controller):
        self.rt_data = controller.rt_data
        s = self.settings = controller.settings
        self.board = board
        self.pins = [
            s.l_echo,
            s.r_echo,
            s.b_echo
        ]
        self.names = [
            'left',
            'right',
            'rear'
        ]
        self.samples = list()
        self.board_pins = list()
        for t, e in self.pins:
            exec('self.board_pins.append((board.D' + str(t) + ', board.D' + str(e) + '))')
            print('self.board_pins.append((board.D' + str(t) + ', board.D' + str(e) + '))')
        self.sensors = list()
        for t, e in self.board_pins:
            self.sensors.append(adafruit_hcsr04.HCSR04(trigger_pin=t, echo_pin=e))

    def ping(self):
        """
        This triggers a sonar ping.
        """
        for name, distance in zip(self.names, self.sensors):
            try:
                self.rt_data['SONAR'][name] = int(distance.distance)
                # if name == 'left':
                print(name, distance.distance)
            except RuntimeError:
                # print('fail')
                pass
            time.sleep(0.1)
