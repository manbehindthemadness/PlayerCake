"""
This holds our programs main loops.
"""
from warehouse.communication import NetCom
from director import settings
from threading import Thread
from warehouse.loggers import dprint
import pprint
import time

rt_data = dict()
term = False


class Start:
    """
    Here we launch our program threads.
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
        self.threads = [
            Thread(target=self.listen, args=()),
        ]
        if settings.Debug:
            self.threads.append(Thread(target=self.debug, args=()))

        for thread in self.threads:  # Launch threads.
            thread.start()

    def debug(self):
        """
        Dumps the real time data to console.
        """
        debug_model = dict()
        for reading in self.rt_data:  # Build debug model.
            if reading in settings.Debug_Filter:
                debug_model[reading] = self.rt_data[reading]
        while not self.term:
            skip_report = False
            if settings.Debug_Update_Only:  # Log update only.
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
                if settings.Debug_Pretty:
                    pprint.PrettyPrinter(indent=4).pprint(debug_model)
                else:
                    for reading in debug_model:
                        if reading in settings.Debug_Filter:
                            print(reading, debug_model[reading], '\n')
            time.sleep(settings.Debug_Cycle)

    def close(self):
        """
        Closes threads.
        """
        self.netcom.close()  # Release network sockets
        self.term = True

    def listen(self):
        """
        This starts the tcp server, listens for incoming connections and transports the data into the real time model.
        """
        listener = self.rt_data['LISTENER'] = dict()

        while not self.term:
            print('waiting for incoming data')
            server = self.netserver()
            self.received_data = server.output

            # noinspection PyBroadException,PyPep8
            try:
                self.sender = self.received_data['SENDER']
                if self.sender in self.settings.Paired_Stages:  # Identify incoming connection.
                    listener[self.sender] = self.received_data['DATA']  # Send received data to real time model.
                else:
                    dprint(self.settings, ('Unknown client connection:', self.sender))  # Send to debug log
            except KeyError as err:
                print(err)
                dprint(self.settings, ('Malformed client connection:', self.sender))  # Send to debug log
                pass
