"""
This is where we will keep the code used to update various displays used across the platforms.

https://stackoverflow.com/questions/50288467/how-to-set-up-the-baud-rate-for-i2c-bus-in-linux  # recompile device tree for new i2c clock speed
"""
from luma.core.render import canvas
from PIL import ImageFont
import sys
import logging
from luma.core import cmdline, error
import os


# logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)-15s - %(message)s'
)
# ignore PIL debug messages
logging.getLogger('PIL').setLevel(logging.ERROR)


def display_settings(args):
    """
    Display a short summary of the settings.
    :rtype: str
    """
    iface = ''
    display_types = cmdline.get_display_types()
    if args.display not in display_types['emulator']:
        iface = 'Interface: {}\n'.format(args.interface)

    lib_name = cmdline.get_library_for_display_type(args.display)
    if lib_name is not None:
        lib_version = cmdline.get_library_version(lib_name)
    else:
        lib_name = lib_version = 'unknown'

    import luma.core
    version = 'luma.{} {} (luma.core {})'.format(
        lib_name, lib_version, luma.core.__version__)

    return 'Version: {}\nDisplay: {}\n{}Dimensions: {} x {}\n{}'.format(
        version, args.display, iface, args.width, args.height, '-' * 60)


def get_device(actual_args=None):
    """
    Create device from command-line arguments and return it.
    """
    device = None
    if actual_args is None:
        actual_args = sys.argv[1:]
    parser = cmdline.create_parser(description='PlayerCake Visual Debugger')
    args = parser.parse_args(actual_args)

    if args.config:
        # load config from file
        config = cmdline.load_config(args.config)
        args = parser.parse_args(config + actual_args)

    print(display_settings(args))

    # create device
    try:
        device = cmdline.create_device(args)
    except error.Error as e:
        parser.error(e)

    return device


class Display:
    """
    This is our debug screen controller.
    """
    def __init__(self, controller):
        """
        :param controller: Inherit from real time program.
        :type controller: rt.Start
        """
        self.controller = controller
        self.mode = self.controller.settings.debug_screen_mode
        self.lines = self.controller.lines
        self.device = get_device()
        font_path = os.path.abspath(
            os.path.join(
                # os.path.dirname(__file__), 'fonts', 'C&C Red Alert [INET].ttf'))
                os.path.dirname(__file__), 'fonts', 'code2000.ttf'))
        self.font2 = ImageFont.truetype(font_path, 8)
        self.font3 = ImageFont.truetype(font_path)

    def update(self):
        """
        This updates the screen with new information depending on the screen debugging mode.
        """
        meth = eval('self.' + self.mode)
        meth()

    def text(self):
        """
        This is the micro-console debug mode.

        {
            "1": {
                "x_pos": 0,
                "y_pos": 0,  - This is added by-line into padding.
                "message": "Text to display".
                "font": "my font here", - Defaults to self.font if empty.
                "file": 155, - Defaults to 255 if empty
            },,
            "2": {}, - etc....
        }
        """

        lines = list(self.lines)
        lines.reverse()
        inc = 7
        with canvas(self.device) as draw:
            for idx, line in enumerate(lines[:7]):
                inc += 7
                if not idx:
                    draw.text((0, 3), str(line), font=self.font3, fill="white")
                else:
                    draw.text((0, inc), str(line), font=self.font2, fill="white")

    def stats(self):
        """
        This shows system stats.
        """
        syss = self.controller.rt_data['SYS']
        stats = self.controller.rt_data['SYS']['STATS']
        imu = self.controller.rt_data['IMU']
        gps = self.controller.rt_data['GPS']
        template = {
            '1': {'message': 'CPU:' + str(stats['CPU_LOAD']) + ' ' + 'CPU_T:' + str(syss['CPU_TEMP']) + 'C'},
            '2': {
                'message': 'Mem:' + str(stats['VIRTUAL_MEMORY'].percent) + ' disk:' + str(stats['DISK_IO'].percent)},
            '3': {'message': 'Gyro: X ' + str(round(imu['kalmanX'], 1)) + '\tY ' + str(round(imu['kalmanY'], 1))},
            '4': {'message': 'Heading: ' + str(round(imu['tiltCompensatedHeading'], 5))},
            '5': {'message': 'Lat: ' + str(round(gps['LAT'], 5))},
            '6': {'message': 'Long: ' + str(round(gps['LONG'], 5))},
            '7': {'message': 'Altitude: ' + str(round(gps['ALT'], 5))},
            '8': {'message': 'Pressure: ' + str(round(gps['PRESS'], 1))},
        }
        inc = 0
        with canvas(self.device) as draw:
            for idx, line in enumerate(template):
                text = template[str(idx + 1)]['message']
                draw.text((0, inc), str(text), font=self.font2, fill="white")
                inc += 7
