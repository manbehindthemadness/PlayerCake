"""
This holds our programs main loops.
"""
from warehouse.communication import NetCom
from warehouse.utils import check_dict, update_dict, get_time_secs, fltr_al
from settings import settings
from warehouse.threading import Thread
from warehouse.loggers import dprint, tprint
import traceback
import pprint
import time
import sys
import os
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

rt_data = dict()
term = False


# noinspection DuplicatedCode
class Start:
    """
    Real time program loop.

    Data model specifications:

    {
        "LISTENER": {
            "<STAGE_ID1>": "<Recieved network data>" , TODO: We need to find a way to organize this.
            "<STAGE_ID2>": "<Recieved network data>" ... etc.
        },
        "ADDRESSES": {
            "<STAGE_ID1>": "<Ipaddress>",
            <STAGE_ID2>": "<Ipaddress>"... etc.
        },
    }

    """

    def __init__(self, controller):
        """
        Set initial variables.
        """
        global rt_data
        global term
        self.controller = controller
        self.rt_data = self.controller.rt_data  # Pass real time data
        self.temp = self.rt_data['temp']
        self.connected_stages = self.rt_data['connected_stages'] = dict()  # This will be used to select active stages in the UX.
        self.term = term  # Pass termination.
        self.net_term = False
        self.datastream_term = self.temp['datastream_term']
        self.settings = settings  # Pass settings.
        self.notify = self.controller.notify
        self.notification = controller.notification
        self.reconnecting = False
        self.netcom = NetCom(self)
        self.netclient = self.netcom.tcpclient  # Get client,
        self.netserver = self.netcom.tcpserver  # Get server.
        self.received_data = None
        self.sender = None
        self.command = None
        self.threads = [
            Thread('tcp_server', target=self.listen, args=()),
            Thread('ready_state', target=self.confirm_ready_state, args=())
        ]
        if settings.debug:
            self.threads.append(Thread(name='debugger', target=self.debug, args=()))

        for thread in self.threads:  # Launch threads.
            thread.start()

    def debug(self):
        """
        Dumps the real time data to console.

        TODO: THis thing only works the first time!
        """
        time.sleep(5)
        debug_model = dict()
        for reading in self.rt_data:  # Build debug model.
            if reading in settings.debug_filter:
                debug_model[reading] = dict()
        while not self.term:
            tprint(self.settings, 'debug')
            skip_report = False
            if settings.debug_update_only:  # Log update only.
                for reading in self.settings.debug_filter:
                    old = debug_model[reading]
                    new = self.rt_data[reading]
                    if new != old:
                        print('updating debug model')
                        # noinspection PyUnusedLocal
                        debug_model[reading] = self.rt_data[reading]  # No idea why I can't instance these...
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
            time.sleep(settings.debug_cycle)

    def dump(self):
        """This just dumps the real time model to console"""
        pprint.PrettyPrinter(indent=4).pprint(self.rt_data)

    def close(self):
        """
        Closes threads.
        """
        global term
        term = True
        self.term = True
        self.netcom.close()

    def listen(self):
        """
        This starts the tcp server, listens for incoming connections and transports the data into the real time model.
        """
        listener = self.rt_data['LISTENER'] = check_dict(self.rt_data, 'LISTENER')
        addresses = self.rt_data['ADDRESSES'] = check_dict(self.rt_data, 'ADDRESSES')

        while not self.term:
            # print('listening')
            tprint(self.settings, 'listen')
            server = self.netserver()
            self.received_data = server.output
            address = server.client_address
            try:
                self.sender = self.received_data['SENDER']
                # print('receiving data:', self.received_data)
                if self.sender in self.settings.stages.keys():  # Identify incoming connection.
                    # listener[self.sender] = self.received_data['DATA']  # Send received data to real time model.
                    if self.sender not in listener.keys():
                        listener[self.sender] = dict()
                    listener[self.sender] = update_dict(listener[self.sender], self.received_data['DATA'])
                    # print('recieved_data', listener[self.sender])

                    addresses[self.sender] = address  # Store client address for future connections.
                else:
                    dprint(self.settings, ('Unknown client connection:', self.sender))  # Send to debug log.

            except (KeyError, TypeError) as err:
                dprint(self.settings, ('Malformed client connection:', self.sender, err))  # Send to debug log.
                pass
            # print(self.rt_data['ADDRESSES'])
        self.netcom.close()  # Release network sockets.

    def send(self, destination_id, message):
        """
        This transmits a data package to the specified client id.
        """
        if 'SENDER' not in message.keys():
            message['SENDER'] = self.settings.director_id
        addresses = self.rt_data['ADDRESSES']
        if destination_id in addresses.keys():
            address = self.rt_data['ADDRESSES'][destination_id][0]
            self.netclient(message, address + ':' + str(self.settings.tcpbindport))
        else:
            dprint(self.settings, ('Error, client not found: ' + destination_id,))

    def confirm_ready_state(self):
        """This tells stages that we are ready for action"""

        # TODO: I this is where our weird disconnects are coming from, when a stage reconnects before we know it disco.
        while not self.term:
            tprint(self.settings, 'ready')
            stages = check_dict(self.rt_data, 'LISTENER')
            # if 'STATUS' in stages.keys():
            # print(stages)
            client = None
            try:
                for stage in stages:
                    # print('STAGES', len(stages))
                    client = stages[stage]
                    if 'STATUS' not in client.keys():
                        client['STATUS'] = 'ready'  # Handle state check for sudden disconnects.
                    if client['STATUS'] == 'ready':
                        print('sending ready state to', stage)
                        self.send(stage, {'SENDER': self.settings.director_id, 'DATA': {'STATUS': 'confirmed'}})  # Transmit ready state to stage.
                        client['STATUS'] = 'confirmed'
                        dprint(self.settings, ('Handshake with client ' + stage + ' confirmed, starting heartbeat',))
                        self.notification.set('client ' + stage + ' connected')
                        self.notify()
                        exec('self.' + fltr_al(stage) + ' = True')  # Create a dynamic connection variable.
                        if stage not in self.connected_stages.keys():
                            self.connected_stages[stage] = 'self.' + fltr_al(stage)  # Add stage to connected clients list.
                        thread = Thread(name='heartbeat_' + stage, target=self.heartbeat, args=(stage,))
                        thread.start()
                        thread.join(1)
            except (KeyError, ConnectionRefusedError, RuntimeError) as err:
                if isinstance(client, str):
                    track = traceback.format_exc()  # Show full stack.
                    try:
                        self.notification.set('client ' + client + ' failed to connect')
                        self.notify()
                    except TypeError:
                        pass
                    # if self.controller.stage == client:
                    #     print('removing target stage, disconnected')
                    #     self.controller.stagename.set('')
                    #     self.controller.stage_id = None
                    self.disconnect_stage(client)
                    client['STATUS'] = 'disconnected'
                    dprint(self.settings, ('Ready state for client:', client, 'not found, retrying', err))
                    del stages[client]
                    print(track)

            time.sleep(0.3)

    def send_command(self, destination_id, command):
        """
        This allows us to send commands to down-stream stages.
        """
        self.command = {'COMMAND': command}
        message = {'DATA': self.command}
        self.send(destination_id, message)
        return self

    def disconnect_stage(self, stage):
        """
        This removes a stage from the connected_stages dict.
        """
        try:
            del self.connected_stages[stage]
            # self.rt_data['LISTENER'][stage]['STATUS'] = 'disconnected'
        except KeyError:
            pass

    def heartbeat(self, stage_id):
        """
        This is our keepalive thread... Should this be moved to stage?

        :param stage_id: This is the client identifier we are going to monitor.
        :type stage_id: str
        """
        client = True
        listener = self.rt_data['LISTENER']
        time.sleep(2)  # Wait for new heartbeat to arrive.
        retry = 0
        while not self.term and client:
            if stage_id in listener.keys():
                stage = listener[stage_id]
                if 'HEARTBEAT' in stage.keys():
                    beat_time = get_time_secs(stage['HEARTBEAT'])
                    if int(beat_time) >= settings.networktimeout:  # Client is dead :(
                        retry += 1
                        if retry > self.settings.networkretries:
                            self.notification.set('client ' + stage_id + ' disconnected')
                            self.notify()
                            client = False
                            listener[stage_id]['STATUS'] = 'disconected'
                            dprint(self.settings, ('Client:', stage_id, 'has disconnected'))
                            self.disconnect_stage(stage_id)
                            # self.netcom.close()
                            # self.net_term = True
                            self.temp['datastream_term'] = True
                            # time.sleep(2)
                            # self.net_term = False
                            # self.netcom = NetCom(self)
                            # self.netclient = self.netcom.tcpclient  # Get client,
                            # self.netserver = self.netcom.tcpserver  # Get server.
            time.sleep(1)
