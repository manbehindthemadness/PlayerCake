"""
This is where we will keep the code used to update various displays used across the platforms.

https://stackoverflow.com/questions/50288467/how-to-set-up-the-baud-rate-for-i2c-bus-in-linux  # recompile device tree for new i2c clock speed
"""
from luma.core.render import canvas
from PIL import ImageFont
import time
import sys
from textwrap import wrap
# import logging
from luma.core import cmdline, error
import os
from warehouse.utils import percent_in, percent_of, check_dict


# # logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)-15s - %(message)s'
# )
# # ignore PIL debug messages
# logging.getLogger('PIL').setLevel(logging.ERROR)


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

    # print(display_settings(args))

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
        NOTE: Some of these display modes could be simplified; however, I left them this way to ease future alterations.

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
        alt_font_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), 'fonts', 'C&C Red Alert [INET].ttf'))
        self.font1 = ImageFont.truetype(font_path, 9)
        self.font2 = ImageFont.truetype(font_path, 8)
        self.font3 = ImageFont.truetype(font_path)
        self.font4 = ImageFont.truetype(alt_font_path, 60)
        self.font5 = ImageFont.truetype(font_path, 60)
        self.ready_msg = True

    def wait(self):
        """
        This prints a notification, and then waits for a second.
        """
        if self.ready_msg:
            print('realtime model incomplete, waiting')
            self.ready_msg = False
        time.sleep(1)

    def update(self):
        """
        This updates the screen with new information depending on the screen debugging mode.
        """
        self.mode = self.controller.settings.debug_screen_mode
        # print('changing screen to mode:', self.mode)
        try:
            meth = eval('self.' + self.mode)
            meth()
        except TypeError:
            print('invalid settings detected!', self.mode)
            raise TypeError

    @staticmethod
    def stm_prefix(value):
        """
        This just makes a handy stream key prefix.
        """
        return 's_' + str(value)

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
        def breaktext(text, length):
            """
            We will use this to implement line breaks into the debug screen.
            """
            return wrap(str(text), length)

        lines = list(self.lines)
        lines.reverse()
        inc = 7
        with canvas(self.device) as draw:
            # txt = []
            for idx, line in enumerate(lines[:7]):

                if inc <= 49:
                    if not idx:
                        txt = breaktext(line, 23)
                        draw.text((0, 3), txt[0], font=self.font3, fill="white")
                        inc += 2
                    else:
                        inc += 7
                        txt = breaktext(line, 27)
                        draw.text((0, inc), txt[0], font=self.font2, fill="white")
                    if len(txt) > 1:
                        # print(txt)
                        for tx in txt[1:]:
                            inc += 7
                            if inc <= 49:
                                draw.text((0, inc), tx, font=self.font2, fill="white")
        ss = check_dict(self.controller.rt_data, 'SUB_TEXT')
        for idx, line in enumerate(lines[:7]):
            ss['s_' + str(idx)] = line + '\t'

    def stats(self):
        """
        This shows system stats.
        """
        syss = self.controller.rt_data['SYS']
        stats = self.controller.rt_data['SYS']['STATS']
        imu = self.controller.rt_data['IMU']
        gps = self.controller.rt_data['GPS']
        try:
            lat = str(round(gps['LAT'], 5))
            long = str(round(gps['LONG'], 5))
            alt = str(round(gps['ALT'], 5))
            press = str(round(gps['PRESS'], 1))
        except KeyError:
            lat = long = alt = press = '0'
        template = {
            '1': {'message': 'CPU:' + str(stats['CPU_LOAD']) + ' ' + 'CPU_T:' + str(syss['CPU_TEMP']) + 'C'},
            '2': {
                'message': 'Mem:' + str(stats['VIRTUAL_MEMORY'].percent) + ' disk:' + str(stats['DISK_IO'].percent)},
            '3': {'message': 'Gyro: X ' + str(round(imu['kalmanX'], 1)) + '\tY ' + str(round(imu['kalmanY'], 1))},
            '4': {'message': 'Heading: ' + str(round(imu['tiltCompensatedHeading'], 5))},
            '5': {'message': 'Lat: ' + lat},
            '6': {'message': 'Long: ' + long},
            '7': {'message': 'Altitude: ' + alt},
            '8': {'message': 'Pressure: ' + press},
        }
        inc = 0
        with canvas(self.device) as draw:
            for idx, line in enumerate(template):
                text = template[str(idx + 1)]['message']
                draw.text((0, inc), str(text), font=self.font2, fill="white")
                inc += 7
        # Build model for director stream.
        ss = check_dict(self.controller.rt_data, 'SUB_STATS')
        for key in template:
            ss['s_' + key] = template[key]['message']

    def adc(self):
        """
        This will draw all the ADC inputs on the screen allowing us to test wiring and configuration.
        """
        try:
            a_inputs = self.controller.rt_data['ADC']
            col_1 = list()
            col_2 = list()
            for port in range(16):
                text = str(port) + ': ' + str(a_inputs['ADCPort' + str(port)])
                if port < 8:
                    col_1.append(text)
                else:
                    col_2.append(text)
            inc = 0
            with canvas(self.device) as draw:
                for ll, r in zip(col_1, col_2):
                    draw.text((0, inc), str(ll), font=self.font2, fill="white")
                    draw.text((64, inc), str(r), font=self.font2, fill="white")
                    inc += 7
            # build model for director stream.
            ss = check_dict(self.controller.rt_data, 'SUB_ADC')
            for idx, (ll, r) in enumerate(zip(col_1, col_2)):
                ss['s_' + str(idx)] = ll + '\t' + r + '\t'
        except KeyError:
            self.wait()

    def pwm(self):
        """
        This will draw two columns of PWM values.
        """
        try:
            p_outputs = self.controller.rt_data['PWM']['RAD']
            col_1 = list()
            col_2 = list()
            for port in range(16):
                pt = str(port)
                text = pt + ': '
                if pt in p_outputs.keys():
                    text += str(p_outputs[pt])
                else:
                    text += '0'
                if port < 8:
                    col_1.append(text)
                else:
                    col_2.append(text)
            inc = 0
            with canvas(self.device) as draw:
                for ll, r in zip(col_1, col_2):
                    draw.text((0, inc), str(ll), font=self.font2, fill="white")
                    draw.text((64, inc), str(r), font=self.font2, fill="white")
                    inc += 7
                # build model for director stream.
                ss = check_dict(self.controller.rt_data, 'SUB_PWM')
                for idx, (ll, r) in enumerate(zip(col_1, col_2)):
                    ss['s_' + str(idx)] = ll + '\t' + r + '\t'
        except KeyError:
            self.wait()

    def pwmadc(self):
        """
        This shows the pwm value in contrast to it respective adc value.
        """
        def get_spec(leg, p_outs, a_ins):
            """
            This will pull the specified legs pwm and adc ports.
            This will return a list with a series of tuples for x y z and foot.
            [
                [x pwm, x adc],
                ...
            ]
            """
            def get_pwm(lg, p_out, ax):
                """
                This will get us a pwm value based on a leg's axis.
                """
                if len(ax) == 1:
                    ret = str(p_out[str(lg[ax]['pwm'])])
                else:
                    ret = ''
                return ret

            def get_adc(lg, a_in, ax):
                """
                This will get us an adc value based on a legs axis.
                """
                ret = str(a_in['ADCPort' + str(lg[ax]['adc'])])
                return ret
            result = list()
            for axis in ['x', 'y', 'z', 'foot']:
                pw = get_pwm(leg, p_outs, str(axis))
                ad = get_adc(leg, a_ins, str(axis))
                result.append(
                    (axis + ': ' + pw, ad)
                )
            return result

        def make_cols(col_a, col_b, specs):
            """
            This iterates through a list of tuples supplied from get_spec and adds it to the respective columns.
            """
            for spec in specs:
                a, b = spec
                col_a.append(a)
                col_b.append(b)

        try:
            l_defaults = self.controller.settings.legs
            p_outputs = self.controller.rt_data['PWM']['RAD']
            a_inputs = self.controller.rt_data['ADC']
            col_1 = list()
            col_2 = list()
            col_3 = list()
            col_4 = list()
            l_1 = ['LEG1', 'LEG3']
            l_2 = ['LEG2', 'LEG4']
            for l_leg, r_leg in zip(l_1, l_2):
                l_spec = l_defaults[l_leg]
                r_spec = l_defaults[r_leg]
                l_vals = get_spec(l_spec, p_outputs, a_inputs)
                r_vals = get_spec(r_spec, p_outputs, a_inputs)
                make_cols(col_1, col_2, l_vals)
                make_cols(col_3, col_4, r_vals)
            inc = 0
            # build model for director stream.
            ss = check_dict(self.controller.rt_data, 'SUB_PWMADC')
            with canvas(self.device) as draw:
                for idx, (l1, l2, l3, l4) in enumerate(zip(col_1, col_2, col_3, col_4)):
                    draw.text((0, inc), str(l1), font=self.font2, fill="white")
                    draw.text((32, inc), str(l2), font=self.font2, fill="white")
                    draw.text((64, inc), str(l3), font=self.font2, fill="white")
                    draw.text((96, inc), str(l4), font=self.font2, fill="white")
                    ss['s_' + str(idx)] = str(l1) + '\t' + str(l2) + '\t' + str(l3) + '\t' + str(l4) + '\t'
                    inc += 7
        except KeyError as err:
            print(err)
            self.wait()

    def sonar(self):
        """
        This allows us to debug the echolocation sensors.
        """
        def solve(direction, value):
            """
            This solves the position of the bars on the graph.
            """
            def_l = 0
            def_r = 119
            def_b = 31
            bmax = 50
            offset = 0
            if value > 100:
                value = 100
            elif not value:
                value = 1
            if direction == 'left':
                offset = def_l + ((100 - percent_in(value, def_r)) / 2)
            elif direction == 'right':
                offset = def_r - ((100 - percent_in(value, def_r)) / 2)
            elif direction == 'rear':
                offset = def_b - (bmax - (percent_of(value, bmax) / 2))
            if offset > 100:
                offset = 100
            return offset

        with canvas(self.device) as draw:
            sn = self.controller.rt_data['SONAR']
            for dirr in sn:
                shift = solve(dirr, sn[dirr])
                if dirr == 'rear':
                    draw.text((31, shift), '__', font=self.font4, fill="white")
                else:
                    draw.text((shift, 0), '|', font=self.font5, fill="white")

    def gyro(self):
        """
        This is where we debug the IMU/gyro.
        """
        um = [
            'heading',
            'CFangleX',
            'CFangleY',
            'tiltCompensatedHeading',
        ]
        imu_data = self.controller.rt_data['IMU']
        sensor_data = self.controller.rt_data['9DOF']
        inc = 0
        # build model for director stream.
        ss = check_dict(self.controller.rt_data, 'SUB_GYRO')
        ss_idx = 0
        with canvas(self.device) as draw:
            for sensor in sensor_data:
                snc = str(sensor)[0:5]
                draw.text((0, inc), snc + ':    ', font=self.font2, fill="white")
                data = sensor_data[sensor]
                dta = snc + ':'  # update stream model.

                if isinstance(data, tuple):
                    idx = 36
                    for val in list(data):
                        draw.text((idx, inc), str(round(val, 2)), font=self.font2,
                                  fill="white")
                        idx += 23
                        dta += '\t' + str(round(val, 2)) + '\t'  # Update stream model.
                else:
                    draw.text((36, inc), str(round(sensor_data[sensor], 2)), font=self.font2, fill="white")
                    dta += str(round(sensor_data[sensor], 2))
                inc += 8
                ss[self.stm_prefix(ss_idx)] = dta
                ss_idx += 1
            for value in um:
                dta = value + ': ' + str(imu_data[value])[0:5]
                draw.text((0, inc), dta + ':    ', font=self.font2, fill="white")
                inc += 8
                ss[self.stm_prefix(ss_idx)] = dta  # Update stream model.
                ss_idx += 1

    def gyro_calibrate(self):
        """
        This performs calibrations on our backup IMU and the real time 9DOF.
        """
        calibrate = self.controller.calibrate.track()
        # build model for director stream.
        ss = check_dict(self.controller.rt_data, 'SUB_GYRO_CALIBRATE')
        with canvas(self.device) as draw:
            inc = 0
            cnt = 0
            draw.text((100, inc), 'IMU', font=self.font2, fill="white")
            st_line_1 = str()
            st_line_2 = str()
            st_line_3 = str()
            for line in calibrate.report:
                draw.text((0, inc), line, font=self.font2, fill="white")
                ln = line.strip()
                if cnt in [0, 1]:
                    st_line_1 += '' + ln + ' '
                elif cnt in [2, 3]:
                    st_line_2 += '' + ln + '\t'
                else:
                    st_line_3 += '' + ln + '\t'
                inc += 7
                cnt += 1
            draw.text((0, inc), str(calibrate.calibration_status), font=self.font2, fill="white")
            draw.text((100, inc), '9DOF', font=self.font2, fill="white")
            draw.text((0, inc + 7), str(calibrate.status), font=self.font2, fill="white")
            ss['s_0'] = 'BerryGPS - IMU'  # Update stream model.
            ss['s_1'] = st_line_1  # Update stream model.
            ss['s_2'] = st_line_2  # Update stream model.
            ss['s_3'] = st_line_3  # Update stream model.
            ss['s_4'] = 'BNO055 - 9DOF'  # Update stream model.
            ss['s_5'] = calibrate.calibration_status  # Update stream model.
            ss['s_6'] = calibrate.status  # Update stream model.
            time.sleep(0.5)
