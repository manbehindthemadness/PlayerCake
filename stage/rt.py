"""
This file contains the realtime sensor loop.

TODO: Enhance debudder to use on-board reporting screen.
"""

# from stage import settings
from stage.settings import settings
from stage.commands import Command
from stage.improvisors.berryimu import ReadIMU, ReadAlt
from stage.improvisors.gps_lkp import ReadGPS
from stage.improvisors.adc import MCP3008
from stage.improvisors.hcsr04 import Sonar
from stage.improvisors.bno055 import BNO055
from stage.improvisors.calibrations import SetGyros
from stage.actors.servo import InitLeg
import RPi.GPIO as GPIO
from threading import Thread
import time

import datetime
import pprint
import socket
from warehouse.display import Display
from warehouse.utils import check_dict, Fade, update_dict
from warehouse.system import get_cpu_temperature, get_system_stats
from warehouse.communication import NetScan, NetCom
from warehouse.loggers import dprint, tprint


rt_data = dict()
term = False


if settings.debug:
    GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(settings.cooling_fan, GPIO.OUT)  # Init cooling fan.
GPIO.output(settings.cooling_fan, 0)
GPIO.setup(settings.gps_sync, GPIO.IN)  # Setup GPS sync.
GPIO.setup(settings.gps_enable, GPIO.OUT)  # Setup GPS enable.
GPIO.output(settings.gps_enable, 1)  # Init GPS to acquire initial fix.


class Start:
    """
    Real time program loop.

    Data model specifications:

    {{   '9DOF': {   'accelerometer': (0.09, -0.45, 9.42),
                'euler': (279.4375, -0.0625, 2.75),
                'linear_acceleration': (0.12, 0.01, -0.34),
                'quaternion': (   -0.0191650390625,
                                  -0.01531982421875,
                                  0.64617919921875,
                                  0.7628173828125)},
    'ADC': {   'ADCPort0': 172,
               'ADCPort1': 99,
               'ADCPort10': 351,
               'ADCPort11': 332,
               'ADCPort12': 237,
               'ADCPort13': 311,
               'ADCPort14': 363,
               'ADCPort15': 334,
               'ADCPort2': 144,
               'ADCPort3': 142,
               'ADCPort4': 100,
               'ADCPort5': 117,
               'ADCPort6': 143,
               'ADCPort7': 139,
               'ADCPort8': 135,
               'ADCPort9': 140},
    'ADDRESSES': {},
    'GPS': {   'ALT': 45.833050081662506,
               'LAT': 0.0,
               'LONG': 0.0,
               'PRESS': 100775.70756802488,
               'TEMP': 25.735195895191282},
    'IMU': {   'AccXangle': 2.5372963549633774,
               'AccYangle': 0.6210704346177636,
               'CFangleX': 2.4651977476566262,
               'CFangleY': 0.46314554617227544,
               'gyroXangle': -11.240688130000006,
               'gyroYangle': -1.99744678,
               'gyroZangle': -0.6516236999999999,
               'heading': 176.88789014246944,
               'kalmanX': 2.7539779783126717,
               'kalmanY': 0.40895164392733435,
               'tiltCompensatedHeading': 177.11464821569282},
    'LISTENER': {   '6efc1846-d015-11ea-87d0-0242ac130003': {   'COMMAND': {},
                                                                'STATUS': 'ready'},
                    'a9b3cfb3-c72d-4efd-993d-6c8dccbb8609': {   'STATUS': 'ready'}},
    'PWM': {   'GRIDS': {'1': {}, '2': {}, '3': {}, '4': {}},
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
                          '9': 90},
               'XYZ': {   '0': (0, 0, 0),
                          '1': (0, 0, 0),
                          '10': (0, 0, 0),
                          '11': (0, 0, 0),
                          '12': (0, 0, 0),
                          '13': (0, 0, 0),
                          '14': (0, 0, 0),
                          '15': (0, 0, 0),
                          '2': (0, 0, 0),
                          '3': (0, 0, 0),
                          '4': (0, 0, 0),
                          '5': (0, 0, 0),
                          '6': (0, 0, 0),
                          '7': (0, 0, 0),
                          '8': (0, 0, 0),
                          '9': (0, 0, 0)}},
    'SONAR': {'left': 10, 'rear': 23, 'right': 27},
    'SYS': {   'CPU_TEMP': 39.2,
               'STATS': {   'BOOT_TIME': 1602248660.0,
                            'CPU_LOAD': 20.4,
                            'CPU_TIMES': scputimes(user=2575.48, nice=0.56, system=910.82, idle=346323.84, iowait=16.83, irq=0.0, softirq=29.09, steal=0.0, guest=0.0, guest_nice=0.0),
                            'DISK_IO': sdiskusage(total=31214379008, used=3633971200, free=26279493632, percent=12.1),
                            'SENSORS': {   'BATTERY': None,
                                           'FANS': searching for connection...{},
                                           'TEMPS': {   'cpu_thermal': [   shwtemp(label='', current=39.166, high=None, critical=None)]}},
                            'SWAP_MEMORY': sswap(total=104853504, used=0, free=104853504, percent=0.0, sin=0, sout=0),
                            'VIRTUAL_MEMORY': svmem(total=1016561664, available=860155904, percent=15.4, used=87343104, free=684986368, active=218804224, inactive=46653440, buffers=65994752, cached=178237440, shared=6770688, slab=49090560)}}}

    """
    def __init__(self):
        global rt_data
        global term
        self.datastream_term = False
        self.scanning = False
        self.sending = False
        self.lines = ['system init']
        self.settings = settings
        self.rt_data = rt_data  # Pass realtime data.
        self.execute = Command(self).execute
        listener = self.rt_data['LISTENER'] = dict()
        listener[settings.director_id] = dict()
        listener[settings.stage_id] = dict()
        self.screen_mode = 'test'
        self.display = Display(self)
        self.term = term  # Pass termination.
        self.rt_data['9DOF'] = dict()
        self.dof = BNO055(self)  # Init DOF
        self.gac = ReadIMU(self)  # Init IMU.
        self.gps = ReadGPS()  # Init GPS.
        self.alt = ReadAlt()  # Init altimiter.
        self.calibrate = SetGyros(self)
        self.temp = get_cpu_temperature  # Pull CPU temps.
        self.stats = get_system_stats  # Read system info.
        self.reconnecting = False
        self.netscan = NetScan
        self.net_term = False
        self.netcom = NetCom(self)
        self.netclient = self.netcom.tcpclient  # Get client,
        self.netserver = self.netcom.tcpserver  # Get server.
        self.netterm = self.netcom.close
        self.received_data = None
        self.sender = None
        self.server_address = None
        self.connected = False
        self.command = None
        self.imud = None
        self.addresses = self.rt_data['ADDRESSES'] = check_dict(self.rt_data, 'ADDRESSES')
        self.sonar = Sonar(self)

        self.threads = [  # Create threads.
            Thread(target=self.read_adc, args=(), daemon=True),
            Thread(target=self.read_imu, args=()),
            Thread(target=self.read_9dof, args=()),
            Thread(target=self.read_system, args=()),
            Thread(target=self.read_networks, args=()),
            Thread(target=self.read_gps, args=()),
            Thread(target=self.listen, args=()),
            Thread(target=self.send_ready_state, args=()),
            Thread(target=self.command_parser, args=(), daemon=True),
            Thread(target=self.read_sonar, args=''),
            Thread(target=self.command_pwm, args=()),
        ]
        if settings.debug:
            self.threads.append(Thread(target=self.debug, args=()))

        for thread in self.threads:  # Launch threads.
            thread.start()

        # self.init_leg = InitLeg(self, 1)  # This is for testing.

        self.lines.append('system init complete')

    def wait(self):
        """
        This just waits until the signal is true.
        """
        while self.scanning:
            # print('waiting')
            time.sleep(1)

    def wait_send(self):
        """
        This just waits until the signal is true.
        """
        while self.sending:
            # print('send_waiting')
            time.sleep(1)

    def listen(self):
        """
        This starts the tcp server, listens for incoming connections and transports the data into the real time model.
        """
        self.lines.append('launching listener thread')
        listener = self.rt_data['LISTENER'] = check_dict(self.rt_data, 'LISTENER')
        addresses = self.addresses

        while not self.term:  # Start loop.
            self.wait()  # Prevent communication while performaing a net scan.
            tprint(self.settings, 'listen')
            server = self.netserver()
            self.received_data = server.output
            address = server.client_address
            # noinspection PyBroadException,PyPep8
            self.sending = True  # Set send wait flag.
            try:
                self.sender = self.received_data['SENDER']
                # print('receiving data:', self.received_data)
                if self.sender in self.settings.director_id:  # Identify incoming connection.
                    # listener[self.sender] = self.received_data['DATA']  # Send received data to real time model.
                    if self.sender not in listener.keys():
                        listener[self.sender] = dict()
                    listener[self.sender] = update_dict(listener[self.sender], self.received_data['DATA'])

                    if self.sender not in addresses.keys():
                        addresses[self.sender] = address  # Store client address for future connections.
                else:
                    dprint(self.settings, ('Unknown client connection:', self.sender))  # Send to debug log.
                    self.lines.append('client unknown')
            except (KeyError, TypeError) as err:
                dprint(self.settings, ('Malformed client connection:', self.sender, err))  # Send to debug log.
                dprint(self.settings, (self.received_data,))
                self.lines.append('listener malformed')
                time.sleep(0.1)
            self.sending = False  # Set send wait flag.
            # print(self.rt_data['ADDRESSES'])
        self.netcom.close()  # Release network sockets.

    def send(self, message):
        """
        This transmits a data package to the specified client id.
        """
        self.wait()  # Prevent communication while performaing a net scan.
        destination_id = self.settings.director_id
        addresses = self.rt_data['ADDRESSES']
        # self.lines.append('transmitting data')
        self.sending = True  # Set send wait flag.
        try:
            if destination_id in addresses.keys():
                # print('Address detected, using:', self.rt_data['ADDRESSES'][destination_id][0])
                address = self.rt_data['ADDRESSES'][destination_id][0]
                self.netclient(message, address + ':' + str(self.settings.tcpbindport))
            else:
                address = self.netclient(message).address
                self.addresses[destination_id] = address
        except ConnectionResetError as err:
            dprint(self.settings, ('Connection dropout, retrying', err))
            self.lines.append('connection reset')
            self.send(message)
        self.sending = False  # Set send wait flag.
        return self.netclient

    def send_disconnect_notification(self):
        """
        This notifies the director that we are disconnecting.
        Used for power downs...etc.
        """
        self.send({'SENDER': self.settings.stage_id, 'DATA': {'STATUS': 'disconnected'}})

    def send_ready_state(self):
        """This tells the director we are online and ready"""
        self.lines.append('launching state thread')
        self.connected = False
        ready = {'STATUS': 'ready'}
        fail = 0
        while not self.term:  # Start loop.
            if not self.connected:
                self.rt_data['LISTENER'][self.settings.stage_id] = ready
                dir_status = self.rt_data['LISTENER'][self.settings.director_id]
                if 'STATUS' not in dir_status.keys():  # This fixes rapid disconnect reconnects.
                    self.rt_data['LISTENER'][self.settings.director_id]['STATUS'] = 'ready'
                try:
                    self.send({'SENDER': self.settings.stage_id, 'DATA': ready})  # Transmit ready state to director.
                    time.sleep(1)
                    # print(self.rt_data['LISTENER'])
                    try:
                        if self.rt_data['LISTENER'][self.settings.director_id]['STATUS'] == 'confirmed':  # TODO: This seems to be an issue where director stops broadcasting.
                            print('Handshake with director confirmed, starting heartbeat')
                            self.lines.append('handshake confirmed')
                            # self.lines.append('starting heartbeat')
                            self.connected = True
                            # TODO: We should nest another while loop here to autometically send keepalive and determine connection stability.
                            failures = 0
                            while self.connected and not self.term:  # Start loop.
                                try:
                                    # print('sending heartbeat')
                                    self.send({'SENDER': self.settings.stage_id, 'DATA': {'HEARTBEAT': str(datetime.datetime.utcnow())}})  # Transmit ready state to director.
                                    failures = 0
                                except (TimeoutError, socket.timeout):  # Retry on timeout.
                                    print('heartbeat timeout, retrying')
                                    failures += 1  # Up failure count.
                                    pass
                                if failures >= settings.networktimeout:
                                    print('connection failure, attempting to reacquire director.')
                                    self.lines.append('connection failure')
                                    self.lines.append('reconnecting')
                                    self.connected = False
                                    self.rt_data['LISTENER'][self.settings.director_id]['STATUS'] = 'disconnected'
                                    del self.rt_data['ADDRESSES'][self.settings.director_id]
                                time.sleep(1)
                        fail = 0
                    except ValueError:
                        print('realtime model incomplete, retrying')
                except (TimeoutError, socket.timeout) as err:  # Retry on timeout.
                    fail += 1
                    if fail > 20:
                        self.netcom.reconnect()
                    dprint(self.settings, ('Connection timeout', err))
                    self.lines.append('connection timeout')
                    pass
            elif self.rt_data['LISTENER'][self.settings.director_id]['STATUS'] == 'ready':  # This will allow us to re-confirm after connection dropouts.
                self.connected = False
            time.sleep(1)

    def send_datastream(self, message, cycle_time):
        """
        This will initiate a real time datastream upload to the director.
        """
        def transmitter(slf, msg, ct):
            """
            This is our transmitter loop.
            """
            while not slf.datastream_term and self.connected:  # Loop to transmit data stream.
                # print('transmitting stream')
                tm = 0
                while tm <= 10 and slf.reconnecting:  # Pause with timeout if we lose connection.
                    time.sleep(1)
                    if tm == 10:
                        slf.datastream_term = True  # Send termination signal.
                        break  # Break loop and close thread.
                    else:
                        tm += 1
                # print('EVALUATION', 'self.rt_data' + str(msg))
                msgs = msg.split("[")[-1][1:-2]  # Pull out remote key name.
                slf.send({'SENDER': slf.settings.stage_id, 'DATA': {msgs: eval('slf.rt_data' + str(msg))}})  # Send data.
                time.sleep(ct)  # Wait for cycle time.
            slf.datastream_term = False  # Reset term signal and close.
            if not self.connected:
                print('connection lost')
            print('closing datastream\n', 'term', slf.datastream_term, 'status', slf.connected)
        print('starting datastream')
        t = Thread(target=transmitter, args=(self, message, cycle_time,))
        t.start()

    def command_parser(self):
        """
        This is where we check for commands that are issued be the director.
        """
        self.lines.append('launching command thread')
        while not self.term:
            commands = self.rt_data['LISTENER'][settings.director_id]
            check_dict(commands, 'COMMAND')  # Confirm the key exists.
            self.command = commands['COMMAND']
            if self.command:  # Check for command.
                Thread(target=self.execute, args=(self.command,)).start()
                # commands['COMMAND'] = ''  # Clear command after execution.
                del commands['COMMAND']
            time.sleep(0.1)

    def dump(self):
        """This just dumps the real time model to console"""
        self.lines.append('dumping rt model')
        pprint.PrettyPrinter(indent=4).pprint(self.rt_data)

    def close(self):
        """
        Closes threads.
        """
        self.netterm()
        self.term = True

    def debug(self):
        """
        This dumps the rt_data information to console.
        """
        self.lines.append('launching debug thread')
        display = self.display
        time.sleep(5)  # Wait for rt_data to populate.
        debug_model = dict()
        for reading in self.rt_data:  # Build debug model.
            if reading in settings.debug_filter:
                debug_model[reading] = self.rt_data[reading]
        while not self.term:  # Start loop.
            skip_report = False
            if not settings.debug_to_screen:
                try:
                    if settings.debug_update_only:  # Log update only.
                        for reading in debug_model:
                            old = debug_model[reading]
                            new = self.rt_data[reading]
                            if new and new != old:
                                # noinspection PyUnusedLocal
                                old = new
                            else:
                                skip_report = True
                    else:  # Log direct.
                        debug_model = self.rt_data
                    if not skip_report:
                        if settings.debug_pretty:
                            pprint.PrettyPrinter(indent=4).pprint(debug_model)
                        else:
                            for reading in debug_model:
                                if reading in settings.debug_filter:
                                    print(reading, debug_model[reading], '\n')
                except RuntimeError:
                    pass
            else:
                display.update()
            time.sleep(settings.debug_cycle)

    def read_adc(self):
        """
        Here is where we read the ADC inputs in real-time.
        """
        self.lines.append('launching adc thread')
        self.rt_data['ADC'] = dict()
        mcp = MCP3008(self)
        while not self.term:
            try:
                mcp.scan()
            except TypeError:
                print('unable to read ADC, skipping')

    def read_imu(self):
        """
        Here is where we read the accel/mag/gyro/alt/temp.

        NOTE: This is for the backup gyro, not the real time unit, the real time data is acquired within read_9dof.
        """
        self.lines.append('launching imu thread')
        self.imud = check_dict(self.rt_data, 'IMU')
        gac = self.gac

        while not self.term:
            dbg = str()
            for rt_value in gac.rt_values:
                eval_str = "self.imud['" + rt_value + "'] = gac.getvalues()." + rt_value
                exec(eval_str)
                if self.settings.debug_imu:
                    dbg += str(rt_value) + ':' + str(self.imud[str(rt_value)]) + '  '
            # print(self.imud['heading'])
            if self.settings.debug_imu:
                # print(dbg, '\n', self.rt_data['9DOF']['accelerometer'])
                # i = self.rt_data['IMU']
                # print(i['gyroXangle'], i['gyroYangle'], i['gyroZangle'])
                # print(self.rt_data['9DOF']['gyroscope'], '\n')
                time.sleep(1)

    def read_9dof(self):
        """
        This is where we get the real time 9dof information.
        """
        rd = 0
        while not self.term:
            self.dof.read()
            time.sleep(self.settings.dof_cycle)
            if rd == 100000:
                # print('saving calibration')
                self.dof.save_calibration()  # TODO: Inspect for performance.
                rd = 0
            else:
                rd += 1

    def read_system(self):
        """
        This is where we read values in relation to the running system itself.
        """
        self.lines.append('launching system thread')
        sys = check_dict(self.rt_data, 'SYS')
        while not self.term:
            sys['CPU_TEMP'] = self.temp()
            sys['STATS'] = self.stats()
            time.sleep(settings.system_cycle)

    def read_networks(self):
        """
        This is where we perform out wireless network scans. This is placed here because it takes longer to run depending
        on the amount of information that neads to be read.
        """
        self.lines.append('launching network thread')
        sys = check_dict(self.rt_data, 'SYS')
        while not self.term:
            self.wait_send()  # Wait for existing connections to close.
            # print('starting scan')
            self.scanning = True  # Set scanning flag.
            time.sleep(1)
            sys['NETWORKS'] = self.netscan().data
            # print('scanning complete')
            self.scanning = False  # Set scanning flag.
            time.sleep(settings.netscan_cycle)

    def read_gps(self):
        """
        Here is where we gather GPS location data.
        """
        self.lines.append('launching gps thread')
        gps = check_dict(self.rt_data, 'GPS')
        alt = self.alt
        lat_vals = list()
        long_vals = list()
        while not self.term:
            if GPIO.input(settings.gps_sync):
                try:
                    gps_dat = self.gps.getpositiondata()
                    lats = Fade(settings.gps_fade, lat_vals, gps_dat.lat)
                    gps['LAT'] = lats[0]
                    lat_vals = lats[1]
                    longs = Fade(settings.gps_fade, long_vals, gps_dat.long)
                    gps['LONG'] = longs[0]
                    long_vals = longs[1]
                    alt_data = alt.get_temperature_and_pressure_and_altitude()
                    gps['ALT'] = alt_data.altitude / 100
                    gps['PRESS'] = alt_data.pressure / 100
                    gps['TEMP'] = alt_data.temperature / 100
                except (ValueError, IndexError):
                    dprint(settings, ('GPS telemetry error, invalid data',))
        time.sleep(self.settings.gps_delay)

    def read_sonar(self):
        """
        This captures our sonar data and stores it in the real time model.
        """
        self.rt_data['SONAR'] = dict()
        while not self.term:
            self.sonar.ping()
            time.sleep(settings.sonar_cycle)

    def command_pwm(self):
        """
        This is where we will set the pwm values that drive our servos.

        Servo control will be achieved in three parts of the real time data model:
            1. We will have a section that stores the raw pwm values that are read to the controller.
            2. we will have pre-rendered local grids that sport the pwm values required to achieve a specific XYZ position.
            3. we will have a command section that contains the XYZ values that the plotter instructs so we follow our trajectory.
        'PWM': {
            'GRIDS': {
                'LEG1': '<grid data>',  # dict
                'LEG2': ...
            },
            'RAD': {
                '0': '<pwm value>',  # int
                '1': ...
            },
            'XYZ': {
                '0': '(<x value>, <y value>, <z value>)',  # tuple of ints
                '1': ...
            }
        }
        """
        leg_defaults = self.settings.legs
        pwmdt = self.rt_data['PWM'] = dict()
        grids = pwmdt['GRIDS'] = dict()
        for leg in range(4):  # Populate local grids.
            leg = str(leg + 1)
            exec('leg = "LEG' + leg + '"')  # TODO: This is where we will place the local grid renderer.
            grids[leg] = dict()
        rad = pwmdt['RAD'] = dict()  # Populate radial PWM values.
        for leg in ['LEG1', 'LEG2', 'LEG3', 'LEG4']:  # Here we set the legs to the configured neutral.
            dt = leg_defaults[leg]
            for axis in dt:
                ax = dt[axis]
                if len(axis) == 1:  # TODO: We might have to handle continous rotation here.
                    rad[str(ax['pwm'])] = ax['nu']
        xyz = pwmdt['XYZ'] = dict()  # Populate desired XYZ position.
        for pos in range(16):  # TODO: This is where we will need to translate the default nautral value from RAD.
            xyz[str(pos)] = (0, 0, 0)


if __name__ == '__main__':
    s = Start()
    # s.dump()
