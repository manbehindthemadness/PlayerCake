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
# from stage.improvisors.bmp280 import alt
# from ADCPi import ADCPi, TimeoutError as ADCTimeout
import RPi.GPIO as GPIO
from threading import Thread
import time

import datetime
import pprint
import socket
from warehouse.display import SSD1306
from warehouse.utils import check_dict, Fade, update_dict
from warehouse.system import get_cpu_temperature, get_system_stats
from warehouse.communication import NetScan, NetCom
from warehouse.loggers import dprint, tprint


# noinspection PyArgumentEqualDefault,PyArgumentEqualDefault,PyArgumentEqualDefault
# adc = ADCPi(*settings.ADC_I2C)  # Init ADC.
# adc.set_pga(1)  # Set gain
# adc.set_bit_rate(12)  # Adjust timing (lower is faster)
# adc.set_conversion_mode(1)  # Set continuous conversion

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


# noinspection DuplicatedCode
class Start:
    """
    Real time program loop.

    Data model specifications:

    {
        "LISTENER": {
            "<DIRECTOR_ID>": "<Recieved network data>" , TODO: We need to find a way to organize this.
        },
        "ADC": {"ADCPort1": "value", "ADCPort2": "value"},  # etc...
        "IMU": {
            "AccXangle": "value",
            "AccYangle": "value",
            "gyroXangle": "value",
            "gyroYangle": "value",
            "gyroZangle": "value",
            "CFangleX": "value",
            "CFangleY": "value",
            "kalmanX": "value",
            "kalmanY": "value",
            "heading": "value",
            "tiltCompensatedHeading": "value"
        },
        "GPS": {
            "LAT": "value",
            "LONG": "value",
            "ALT": "value",
            "PRESS": "value",
            "TEMP": "value"
        },
        "SYS": {
            "CPU_TEMP": "value",
            "STATS": {
                "BOOT_TIME": "value",
                "CPU_LOAD": "value",
                "DISK_IO": "value",
                "SENSORS": {
                    "BATTERY": "value",
                    "FANS": "value",
                    "TEMPS": ["value1", "value2"], - etc...
                },
                "SWAP_MEMORY": "value",
                "VIRTUAL_MEMORY": "value"
            },
        },
        "NETWORKS": {
            "Cell1": {
                "address": "value",
                "Authentication Suites": "value",
                "Bit Rates": "value",
                "Channel": "value",
                "ESSID": "value",
                "Encryption key": "value",
                "Extra": "value",
                "Frequency": "value",
                "Group Cipher": "value",
                "IE": "value",
                "Mode": "value",
                "Pairwise Ciphers": "value",
                "Quality": "value"
            },
            "Cell2"{.....), - etc...
        },
        "SCRIPTS": {
            WIP - TBD...
        },
        "ACTORS": {
            WIP - TBD...
        },
    }
    """
    def __init__(self):
        global rt_data
        global term
        self.settings = settings
        self.rt_data = rt_data  # Pass realtime data.
        self.execute = Command(self).execute
        listener = self.rt_data['LISTENER'] = dict()
        listener[settings.directorid] = dict()
        listener[settings.stageid] = dict()
        self.display = SSD1306
        self.term = term  # Pass termination.
        self.gac = ReadIMU  # Init IMU.
        self.gps = ReadGPS  # Init GPS.
        self.alt = ReadAlt  # Init altimiter.
        self.temp = get_cpu_temperature  # Pull CPU temps.
        self.stats = get_system_stats  # Read system info.
        # self.adc = ADCPi(*settings.ADC_I2C)  # Init ADC.
        # self.adc.set_pga(1)  # Set gain.
        # self.adc.set_bit_rate(12)  # Adjust timing (lower is faster).
        # self.adc.set_conversion_mode(1)  # Set continuous conversion.
        self.netscan = NetScan
        self.netcom = NetCom(self.settings)
        self.netclient = self.netcom.tcpclient  # Get client,
        self.netserver = self.netcom.tcpserver  # Get server.
        self.netterm = self.netcom.close
        self.received_data = None
        self.sender = None
        self.server_address = None
        self.connected = False
        self.command = None
        self.addresses = self.rt_data['ADDRESSES'] = check_dict(self.rt_data, 'ADDRESSES')

        self.threads = [  # Create threads.
            Thread(target=self.read_adc, args=()),
            Thread(target=self.read_imu, args=()),
            Thread(target=self.read_system, args=()),
            Thread(target=self.read_networks, args=()),
            Thread(target=self.read_gps, args=()),
            Thread(target=self.listen, args=()),
            Thread(target=self.send_ready_state, args=()),
            Thread(target=self.command_parser, args=()),
        ]
        if settings.debug:
            self.threads.append(Thread(target=self.debug, args=()))

        for thread in self.threads:  # Launch threads.
            thread.start()

    def listen(self):
        """
        This starts the tcp server, listens for incoming connections and transports the data into the real time model.
        """
        listener = self.rt_data['LISTENER'] = check_dict(self.rt_data, 'LISTENER')
        addresses = self.addresses

        while not self.term:  # Start loop.
            tprint(self.settings, 'listen')
            server = self.netserver()
            self.received_data = server.output
            address = server.client_address
            # noinspection PyBroadException,PyPep8
            try:

                self.sender = self.received_data['SENDER']
                # print('receiving data:', self.received_data)
                if self.sender in self.settings.directorid:  # Identify incoming connection.
                    # listener[self.sender] = self.received_data['DATA']  # Send received data to real time model.
                    if self.sender not in listener.keys():
                        listener[self.sender] = dict()
                    listener[self.sender] = update_dict(listener[self.sender], self.received_data['DATA'])

                    if self.sender not in addresses.keys():
                        addresses[self.sender] = address  # Store client address for future connections.
                else:
                    dprint(self.settings, ('Unknown client connection:', self.sender))  # Send to debug log.

            except (KeyError, TypeError) as err:
                dprint(self.settings, ('Malformed client connection:', self.sender, err))  # Send to debug log.
                dprint(self.settings, (self.received_data,))
                pass
            # print(self.rt_data['ADDRESSES'])
        self.netcom.close()  # Release network sockets.

    def send(self, message):
        """
        This transmits a data package to the specified client id.
        """
        destination_id = self.settings.directorid
        addresses = self.rt_data['ADDRESSES']
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
            self.send(message)
        return self.netclient

    def send_ready_state(self):
        """This tells the director we are online and ready"""
        self.connected = False
        ready = {'STATUS': 'ready'}
        while not self.term:  # Start loop.
            if not self.connected:
                self.rt_data['LISTENER'][self.settings.stageid] = ready
                try:
                    self.send({'SENDER': self.settings.stageid, 'DATA': ready})  # Transmit ready state to director.
                    time.sleep(1)
                    if self.rt_data['LISTENER'][self.settings.DirectorID]['STATUS'] == 'confirmed':  # TODO: This guy likes to give up problems when the server malfunctions...
                        print('Handshake with director confirmed, starting heartbeat')
                        self.connected = True
                        # TODO: We should nest another while loop here to autometically send keepalive and determine connection stability.
                        failures = 0
                        while self.connected and not self.term:  # Start loop.
                            try:
                                # print('sending heartbeat')
                                self.send({'SENDER': self.settings.stageid, 'DATA': {'HEARTBEAT': str(datetime.datetime.utcnow())}})  # Transmit ready state to director.
                                failures = 0
                            except (TimeoutError, socket.timeout):  # Retry on timeout.
                                failures += 1  # Up failure count.
                                pass
                            if failures >= settings.networktimeout:
                                print('connection failure, attempting to reacquire director.')
                                self.connected = False
                                self.rt_data['LISTENER'][self.settings.directorid]['STATUS'] = 'disconnected'
                                del self.rt_data['ADDRESSES'][self.settings.directorid]
                            time.sleep(1)
                except (TimeoutError, socket.timeout) as err:  # Retry on timeout.
                    dprint(self.settings, ('Connection failure', err))
                    pass
            elif self.rt_data['LISTENER'][self.settings.directorid]['STATUS'] == 'ready':  # This will allow us to re-confirm after connection dropouts.
                self.connected = False
            time.sleep(1)

    def command_parser(self):
        """
        This is where we check for commands that are issued be the director.
        """

        while not self.term:
            commands = self.rt_data['LISTENER'][settings.directorid]
            check_dict(commands, 'COMMAND')  # Confirm the key exists.
            self.command = commands['COMMAND']
            if self.command:  # Check for command.
                Thread(target=self.execute, args=(self.command,)).start()
                commands['COMMAND'] = ''  # Clear command after execution.

    def dump(self):
        """This just dumps the real time model to console"""
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
        display = self.display()
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
            elif settings.screen_template == 'improv':
                sys = self.rt_data['SYS']
                stats = self.rt_data['SYS']['STATS']
                imu = self.rt_data['IMU']
                gps = self.rt_data['GPS']
                template = {
                    '1': {'message': 'CPU%:' + str(stats['CPU_LOAD']) + ' ' + 'CPU_T:' + str(sys['CPU_TEMP']) + 'C'},
                    '2': {'message': 'Mem%:' + str(stats['VIRTUAL_MEMORY'].percent) + ' disk%:' + str(stats['DISK_IO'].percent)},
                    '3': {'message': 'Gyro: X ' + str(round(imu['kalmanX'], 1)) + ' Y ' + str(round(imu['kalmanY'], 1))},
                    '4': {'message': 'Heading: ' + str(round(imu['tiltCompensatedHeading'], 5))},
                    '5': {'message': 'Lat: ' + str(round(gps['LAT'], 5))},
                    '6': {'message': 'Long: ' + str(round(gps['LONG'], 5))},
                    '7': {'message': 'Altitude: ' + str(round(gps['ALT'], 5))},
                    '8': {'message': 'Pressure: ' + str(round(gps['PRESS'], 1))},
                }
                display.text_draw(template)
            time.sleep(settings.debug_cycle)
        self.display().clear()

    def read_adc(self):
        """
        Here is where we read the ADC inputs in real-time.
        """
        self.rt_data['ADC'] = dict()
        MCP3008(self)
        # while not self.term:
        #     try:
        #         for num in range(1, settings.ADC_Num_Channels):
        #             comp = 0
        #             if num in settings.ADC_Ungrounded_Channels:
        #                 comp = settings.ADC_Noise
        #             self.rt_data['ADC']['ADCPort' + str(num)] = adc.read_voltage(num - comp)
        #     except ADCTimeout:
        #         dprint(settings, ('ADC timeout',))
        #         pass

    def read_imu(self):
        """
        Here is where we read the accel/mag/gyro/alt/temp.
        """
        # noinspection PyUnusedLocal
        imud = check_dict(self.rt_data, 'IMU')
        gac = self.gac()
        while not self.term:
            for rt_value in gac.rt_values:
                eval_str = "imud['" + rt_value + "'] = gac.getvalues()." + rt_value
                exec(eval_str)

    def read_system(self):
        """
        This is where we read values in relation to the running system itself.
        """
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
        sys = check_dict(self.rt_data, 'SYS')
        while not self.term:
            sys['NETWORKS'] = self.netscan().data
            time.sleep(settings.netscan_cycle)

    def read_gps(self):
        """
        Here is where we gather GPS location data.
        """
        gps = check_dict(self.rt_data, 'GPS')
        alt = self.alt()
        lat_vals = list()
        long_vals = list()
        while not self.term:
            if GPIO.input(settings.gps_sync):
                try:
                    gps_dat = self.gps().getpositiondata()
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
                except ValueError:
                    dprint(settings, ('GPS telemetry error, invalid data',))
        time.sleep(0.1)
