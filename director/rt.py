"""
This holds our programs main loops.
"""
from warehouse.communication import NetCom
from warehouse.utils import check_dict, update_dict, get_time_secs
from director import settings
from threading import Thread
from warehouse.loggers import dprint, tprint
import pprint
import time
# import datetime

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

    def __init__(self):
        """
        Set initial variables.
        """
        global rt_data
        global term
        self.rt_data = rt_data  # Pass real time data
        self.term = term  # Pass termination.
        self.settings = settings  # Pass settings.
        self.netcom = NetCom(self.settings)
        self.netclient = self.netcom.tcpclient  # Get client,
        self.netserver = self.netcom.tcpserver  # Get server.
        self.received_data = None
        self.sender = None
        self.command = None
        self.threads = [
            Thread(target=self.listen, args=()),
            Thread(target=self.confirm_ready_state, args=())
        ]
        if settings.Debug:
            self.threads.append(Thread(target=self.debug, args=()))

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
            if reading in settings.Debug_Filter:
                debug_model[reading] = dict()
        while not self.term:
            tprint(self.settings, 'debug')
            skip_report = False
            if settings.Debug_Update_Only:  # Log update only.
                for reading in self.settings.Debug_Filter:
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
                if settings.Debug_Pretty:
                    pprint.PrettyPrinter(indent=4).pprint(debug_model)
                else:
                    for reading in debug_model:
                        if reading in settings.Debug_Filter:
                            print(reading, debug_model[reading], '\n')
            time.sleep(settings.Debug_Cycle)

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
            # noinspection PyBroadException,PyPep8
            try:
                self.sender = self.received_data['SENDER']
                # print('receiving data:', self.received_data)
                if self.sender in self.settings.Paired_Stages:  # Identify incoming connection.
                    # listener[self.sender] = self.received_data['DATA']  # Send received data to real time model.
                    if self.sender not in listener.keys():
                        listener[self.sender] = dict()
                    listener[self.sender] = update_dict(listener[self.sender], self.received_data['DATA'])

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
            message['SENDER'] = self.settings.DirectorID
        addresses = self.rt_data['ADDRESSES']
        if destination_id in addresses.keys():
            address = self.rt_data['ADDRESSES'][destination_id][0]
            self.netclient(message, address + ':' + str(self.settings.TCPBindPort))
        else:
            dprint(self.settings, ('Error, client not found: ' + destination_id,))

    def confirm_ready_state(self):
        """This tells stages that we are ready for action"""
        while not self.term:
            tprint(self.settings, 'ready')
            stages = self.rt_data['LISTENER']
            # if 'STATUS' in stages.keys():
            # print(stages)
            client = None
            try:
                for stage in stages:
                    client = stages[stage]
                    if 'STATUS' not in client.keys():
                        client['STATUS'] = 'ready'  # Handle state check for sudden disconnects.
                    if client['STATUS'] == 'ready':
                        print('sending ready state to', stage)
                        self.send(stage, {'SENDER': self.settings.DirectorID, 'DATA': {'STATUS': 'confirmed'}})  # Transmit ready state to stage.
                        client['STATUS'] = 'confirmed'
                        dprint(self.settings, ('Handshake with client ' + stage + ' confirmed, starting heartbeat',))
                        # TODO: start heartbeat thread here.
                        thread = Thread(target=self.heartbeat, args=(stage,))
                        thread.start()
            except (KeyError, ConnectionRefusedError) as err:
                client['STATUS'] = 'disconnected'
                dprint(self.settings, ('Ready state for client:', client, 'not found, retrying', err))
            time.sleep(1)

    def send_command(self, destination_id, command):
        """
        This allows us to send commands to down-stream stages.
        """
        self.command = {'COMMAND': command}
        message = {'DATA': self.command}
        self.send(destination_id, message)
        return self

    def heartbeat(self, stage_id):
        """
        This is our keepalive thread... Should this be moved to stage?

        :param stage_id: This is the client identifier we are going to monitor.
        :type stage_id: str
        """
        client = True
        listener = self.rt_data['LISTENER']
        time.sleep(2)  # Wait for new heartbeat to arrive.
        while not self.term and client:
            if stage_id in listener.keys():
                stage = listener[stage_id]
                if 'HEARTBEAT' in stage.keys():
                    # beat_time = (  # Compare heartbeat times.
                    #         datetime.datetime.utcnow() - datetime.datetime.strptime(
                    #             stage['HEARTBEAT'], '%Y-%m-%d %H:%M:%S.%f'
                    #         )
                    # ).total_seconds()
                    beat_time = get_time_secs(stage['HEARTBEAT'])
                    if int(beat_time) >= settings.NetworkTimeout:  # Client is dead :(
                        client = False
                        listener[stage_id]['STATUS'] = 'disconected'
                        dprint(self.settings, ('Client:', stage_id, 'has disconnected'))
                    # print('beat age', beat_time)
            time.sleep(1)
