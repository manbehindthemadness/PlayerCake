"""
This is where we are going to store all of our communication related code.

TODO: I think we need to implement a serializer for our message contents so we can embed and retrieve complex imformation.

net scan: iwlist wlan0 scanning | egrep 'Cell |Encryption|Quality|Last beacon|ESSID'

"""

import socket
import time
import sys
import re
import os
from cbor2 import loads, dumps
import base64
from threading import Thread
from warehouse.loggers import dprint
from warehouse.utils import open_file


term = False


class NetCom:
    """
    This is the network server module, it contains both TCP and UDP servers.
    Reference:
        https://github.com/ninedraft/python-udp/blob/master/client.py
        https://stackoverflow.com/questions/43475468/windows-python-udp-broadcast-blocked-no-firewall
    """
    def __init__(self, settings):
        self.message = None
        self.settings = settings
        self.types = (bytes, bytearray)

    def encode(self, message):
        """
        Encodes a message using base64 and cbor
        """
        self.message = message
        if not isinstance(self.message, self.types):
            self.message = self.message.encode()
        self.message = loads(
            base64.b64encode(
                self.message
            )
        )

    def decode(self, message):
        """
        Decodes a message using basse64 and cbor.
        """
        self.message = dumps(
            base64.b64decode(
                message
            )
        )

    def udpserver(self):
        """
        Launches a UDP announce server.
        :return: Nothing.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create UDP transmission socket.
        if self.settings.Environment == 'pure':
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        elif self.settings.Environment == 'mixed':  # This is a windows thing...
            server.bind((self.settings.BindAddr, 37020))
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

        server.settimeout(0.2)  # Define server timeout.
        statement = self.settings.Target + ':' + socket.gethostname() + ':' + self.settings.DirectorID + ':' + self.settings.BindAddr + ':' + str(self.settings.TCPBindPort)  # Define data package.
        # TODO: Encode the above information.
        message = bytes(statement, "utf8")  # Convert data package into bytes.
        while not term:  # Broadcast until termination signal is recieved.
            server.sendto(message, ("<broadcast>", 37020))  # Send message.
            # print("message sent!")
            time.sleep(1)

    def tcpserver(self):
        """
        Launches a TCP communication server.
        :return: Nothing.
        """
        global term
        announcethread = Thread(target=self.udpserver, args=())  # Create transmitter thread.
        announcethread.start()  # Launch UDP transmitter.

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.
        server_address = (self.settings.BindAddr, self.settings.TCPBindPort)  # Create connection string.
        dprint(self.settings, ('starting up on %s port %s' % server_address,))
        sock.bind(server_address)  # Bind connection string to socket.
        sock.listen(1)  # Listen for incoming connections.

        while True:
            output = b''
            dprint(self.settings, (sys.stderr, 'waiting for a connection',))
            connection, client_address = sock.accept()  # This waits until a client connects.
            try:
                dprint(self.settings, ('connection from', client_address,))

                while True:  # Receive the data in small chunks and retransmit it
                    data = connection.recv(4096)  # TODO: We need to alter this so we just send back a confirmation, not all data.
                    output += data
                    # print(sys.stderr, 'received "%s"' % data)
                    if data:
                        # print(sys.stderr, 'sending data back to the client')
                        connection.sendall(data)
                    else:
                        dprint(self.settings, (output,))
                        dprint(self.settings, ('no more data from', client_address,))
                        break
            finally:
                connection.close()  # Clean up the connection.
                term = False  # Close transmitter thread.

    def udpclient(self):
        """
        Launches a UDP listener.

        :return: Upstream server connection string.
        :rtype: list
        """
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create UDP client socket.
        if self.settings.Environment == 'pure':
            client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Specify socket options.
            client.bind(("", 37020))  # Bind the socket to all adaptors and the target port.
        elif self.settings.Environment == 'mixed':
            client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Windows compatable version.
            client.bind(("", 37020))  # Bind the socket to all adaptors and the target port.
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

        search = True
        server_info = None
        while search:  # Listen for upstream server to identify itself.
            data, addr = client.recvfrom(1024)
            if self.settings.DirectorID in str(data):  # TODO: revise for cross-application compatibility.
                dprint(self.settings, ("received message: %s" % data,))
                server_info = data.decode("utf8").split(':')
                search = False
        return server_info  # Return upstream server TCP connection information.

    def tcpclient(self, message):
        """
        Launches a TCP client.

        TODO: Find a way to cache the upstream server info.

        :param message: Data to transmit
        :type message: bytes
        :return: Nothing.
        """
        server_info = None
        while not server_info:  # Look for upstream server.
            server_info = self.udpclient()
            dprint(self.settings, ('searching for Director...',))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.

        # print(server_info[3], int(server_info[4]))
        server_address = (server_info[3], int(server_info[4]))  # Collect server connection string.
        dprint(self.settings, ('connecting to %s port %s' % server_address,))
        sock.connect(server_address)  # Connect the socket to the port where the server is listening.
        try:
            # print(sys.stderr, 'sending "%s"' % message)
            sock.sendall(message)  # Send message.

            # Look for the response
            amount_received = 0
            amount_expected = len(message)

            # TODO: We need to alter this so we just send back a confirmation, not all data.
            while amount_received < amount_expected:  # Loop until expected data is recieved.
                data = sock.recv(4096)  # Break data into chunks.
                amount_received += len(data)  # Count collected data.
                # print(sys.stderr, 'received "%s"' % data)

        finally:
            dprint(self.settings, ('closing socket',))
            sock.close()  # Close socket.

    def test(self, _settings):
        """
        Tests the tcpclient.

        :param _settings: Instance of configuration file.
        :type _settings: Module
        :return: Nothing.
        """
        self.tcpclient(bytes(open_file("stage/tests/transmit.log"), "utf8"))


class NetScan:
    """
    Uses iwscan to monitor wifi activity.
    """
    def __init__(self):
        self.raw_data = os.popen("/sbin/iwlist wlan0 scanning").read()
        self.data = dict()
        self.sort()

    def sort(self):
        """
        Takes the contents of raw_data and sorts it into a dictionary.
        """
        p = re.compile(r'\bCell\b.\d+...\bAddress\b').split(self.raw_data)
        last = 'last'
        for cnt, item in enumerate(p):
            item = 'Address' + item
            if cnt > 0:
                entry = self.data['Cell' + str(cnt)] = dict()
                for scnt, row in enumerate(item.splitlines()):
                    value = re.compile(r'[:]|[=]').split(row, 1)
                    if len(row) == 1:
                        value.insert(0, 'Address')
                    for sscnt, val in enumerate(value):
                        value[sscnt] = val.strip()
                    if len(value) == 1:
                        entry[last] = entry[last] + ' ' + value[0]
                    else:
                        entry[value[0]] = value[1]
                        last = value[0]
