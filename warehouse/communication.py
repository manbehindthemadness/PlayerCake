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
import psutil
from cbor2 import loads, dumps
import base64
from threading import Thread
from warehouse.loggers import dprint
from warehouse.utils import open_file


class NetCom:
    """
    This is the network server module, it contains both TCP and UDP servers.
    Reference:
        https://github.com/ninedraft/python-udp/blob/master/client.py
        https://stackoverflow.com/questions/43475468/windows-python-udp-broadcast-blocked-no-firewall
    """
    def __init__(self, settings):
        self.term = False
        self.message = None
        self.settings = settings
        self.types = (bytes, bytearray)
        self.data = bytes()
        self.output = None
        self.bindaddr = GetIP(self.settings).ipv4

        announcethread = Thread(target=self.udpserver, args=())  # Create transmitter thread.
        announcethread.start()  # Launch UDP transmitter.

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.

        if self.settings.Environment == 'mixed':
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_address = (self.bindaddr, self.settings.TCPBindPort)  # Create connection string.
        else:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self.server_address = ('0.0.0.0', self.settings.TCPBindPort)  # Create connection string.
        dprint(self.settings, ('starting up on %s port %s' % self.server_address,))
        self.sock.bind(self.server_address)  # Bind connection string to socket.
        self.sock.listen(1)  # Listen for incoming connections.

    def encode(self, message):
        """
        Encodes a message using base64 and cbor
        """
        self.message = dumps(
                message
        )
        return self

    def decode(self, message):
        """
        Decodes a message using basse64 and cbor.
        """
        self.message = loads(
                message

        )
        return self

    def udpserver(self):
        """
        Launches a UDP announce server.
        :return: Nothing.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create UDP transmission socket.
        if self.settings.Environment == 'pure':
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        elif self.settings.Environment == 'mixed':  # This is a windows thing...
            server.bind((self.bindaddr, 37020))
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

        server.settimeout(0.2)  # Define server timeout.
        statement = self.settings.Role + ':' + socket.gethostname() + ':' + self.settings.DirectorID + ':' + self.bindaddr + ':' + str(self.settings.TCPBindPort)  # Define data package.
        # TODO: Encode the above information.
        # message = bytes(statement, "utf8")  # Convert data package into bytes.
        message = self.encode(statement).message
        while not self.term:  # Broadcast until termination signal is recieved.
            server.sendto(message, ("<broadcast>", 37020))  # Send message.
            # print("message sent!")
            time.sleep(1)

    def tcpserver(self):
        """
        Launches a TCP communication server.
        :return: Nothing.
        """

        self.output = bytes()
        while not self.term:
            dprint(self.settings, (sys.stderr, 'waiting for a connection',))
            connection, client_address = self.sock.accept()  # This waits until a client connects.
            dprint(self.settings, ('connection from', client_address,))
            while True:  # Receive the data in small chunks and retransmit it
                self.data = connection.recv(4096)  # TODO: We need to alter this so we just send back a confirmation, not all data.
                self.output += self.data
                # print(sys.stderr, 'received "%s"' % data)
                if self.data:
                    # print(sys.stderr, 'sending data back to the client')
                    connection.sendall(self.data)
                else:
                    self.output = self.decode(self.output).message
                    dprint(self.settings, (self.output,))
                    dprint(self.settings, ('no more data from', client_address,))
                    connection.close()  # Clean up the connection.
                    break
        print('closing server')

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
            # self.data = data.decode("utf8").split(':')
            self.data = self.decode(data).message.split(':')
            print(self.data)
            if self.data[0] == self.settings.Target and self.data[2] == self.settings.DirectorID:  # TODO: revise for cross-application compatibility.
                dprint(self.settings, ("received message: %s" % data,))
                search = False
        return self.data  # Return upstream server TCP connection information.

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
        message = self.encode(message).message
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

    def test(self):
        """
        Tests the tcpclient.

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


class GetIP:
    """
    Fetches the ipaddress of a local adaptor.
    """
    def __init__(self, settings=None, adaptor=None):
        """
        :param settings: Pass settings file.
        :param adaptor: Optional string value of adaptor.
        """
        if settings:
            self.adaptor = settings.BindAdaptor
        if adaptor:
            self.adaptor = adaptor
        self.data = psutil.net_if_addrs()[self.adaptor]
        self.v4 = self.data[0]
        self.ipv4 = None
        for eth in self.data:
            if str(eth[0]) == 'AddressFamily.AF_INET':
                self.ipv4 = str(eth[1])

