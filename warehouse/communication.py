"""
This is where we are going to store all of our communication related code.

net scan: iwlist wlan0 scanning | egrep 'Cell |Encryption|Quality|Last beacon|ESSID'

https://stackoverflow.com/questions/44029765/python-socket-connection-between-windows-and-linux
https://pythonprogramming.net/python-binding-listening-sockets/

tcpdump -i wlan0 port 30720 -XX

firewall-cmd --direct --add-rule ipv4 filter INPUT 10 -d 255.255.255.255 -j ACCEPT
firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 10 -d 255.255.255.255 -j ACCEPT
firewall-cmd --add-port=37020/udp
firewall-cmd --permanent --add-port=37020/udp

"""

import socket
import time
import re
import os
import psutil
from cbor2 import loads, dumps, CBORDecodeEOF
from threading import Thread
from warehouse.loggers import dprint


class NetCom:
    """
    This is the network server module, it contains both TCP and UDP servers.
    Reference:
        https://github.com/ninedraft/python-udp/blob/master/client.py
        https://stackoverflow.com/questions/43475468/windows-python-udp-broadcast-blocked-no-firewall
    """
    def __init__(self, settings):
        self.term = False
        self.address = None
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

        else:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_address = (self.bindaddr, self.settings.TCPBindPort)  # Create connection string.
        dprint(self.settings, ('starting up on %s port %s' % self.server_address,))
        self.sock.bind(self.server_address)  # Bind connection string to socket.
        self.sock.listen(1)  # Listen for incoming connections.
        self.udpsock = None
        self.client_address = None
        self.connection = None

    def close(self):
        """
        Stops threads and closes out the sockets.
        """
        self.term = True
        # self.sock.shutdown()
        if self.sock:
            self.sock.close()
        if self.udpsock:
            self.udpsock.close()

    def encode(self, message):
        """
        Encodes a message using base64 and cbor.

        TODO: Add encryption here.
        """
        self.message = dumps(
                message
        )
        return self

    def decode(self, message):
        """
        Decodes a message using basse64 and cbor.

        TODO Add decryption here.
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
        self.udpsock = server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create UDP transmission socket.
        if self.settings.Environment == 'pure':
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        elif self.settings.Environment == 'mixed':  # This is a windows thing...
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.bindaddr, self.settings.UDPBroadcastPort))

        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

        server.settimeout(0.2)  # Define server timeout.
        statement = self.settings.Role + ':' + socket.gethostname() + ':' + self.settings.DirectorID + ':' + self.bindaddr + ':' + str(self.settings.TCPBindPort)  # Define data package.
        # TODO: Encode the above information.
        message = self.encode(statement).message
        while not self.term:  # Broadcast until termination signal is recieved.
            server.sendto(message, ("<broadcast>", self.settings.UDPBroadcastPort))  # Send message.
            # print('sending udp message:', message)
            time.sleep(1)

    def tcpserver(self):
        """
        Launches a TCP communication server.
        :return: Nothing.
        """

        self.output = bytes()
        try:
            self.connection, self.client_address = self.sock.accept()  # This waits until a client connects.

            while not self.term:  # Receive the data in small chunks and retransmit it
                self.data = self.connection.recv(4096)  # TODO: We need to alter this so we just send back a confirmation, not all data.
                self.output += self.data
                if self.data:
                    self.connection.sendall(self.data)
                else:
                    try:
                        self.output = self.decode(self.output).message
                    except CBORDecodeEOF:
                        dprint(self.settings, ('Invalid connection data, CBOR EOF, aborting',))
                    self.connection.close()  # Clean up the connection.
                    break
        except OSError:
            pass
        return self

    def udpclient(self):
        """
        Launches a UDP listener.

        :return: Upstream server connection string.
        :rtype: list
        """
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create UDP client socket.
        if self.settings.Environment == 'pure':
            client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Specify socket options.
            client.bind(("", self.settings.UDPBindPort))  # Bind the socket to all adaptors and the target port.
        elif self.settings.Environment == 'mixed':
            client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Windows compatable version.
            client.bind(("", self.settings.UDPBindPort))  # Bind the socket to all adaptors and the target port.
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

        search = True
        while search:  # Listen for upstream server to identify itself.
            data, addr = client.recvfrom(1024)
            self.data = self.decode(data).message.split(':')
            if self.data[0] == self.settings.Target and self.data[2] == self.settings.DirectorID:  # TODO: revise for cross-application compatibility.
                search = False
        return self.data  # Return upstream server TCP connection information.

    def tcpclient(self, message, address=None):
        """
        Launches a TCP client.

        TODO: Find a way to cache the upstream server info.

        :param message: Data to transmit
        :type message:
        :param address: Optional server address and port: 1.2.3.4:5.
        ::type address: str
        :return: Self.
        """
        # dprint(self.settings, ('connection init',))
        server_info = None
        if address:  # Use server address where able.
            server_info = address.split(':')
        while not server_info:  # Look for upstream server.
            dprint(self.settings, ('searching for connection...',))
            server_info = self.udpclient()
        dprint(self.settings, ('connection found:', server_info))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.
        # sock.bind(self.server_address)
        sock.settimeout(self.settings.NetworkTimeout)
        if address:
            server_address = server_info[0], int(server_info[1])
        else:
            server_address = (server_info[3], int(server_info[4]))  # Collect server connection string.
        # dprint(self.settings, ('connecting to %s port %s' % server_address,))
        sock.connect(server_address)  # Connect the socket to the port where the server is listening.
        message = self.encode(message).message
        try:
            sock.sendall(message)  # Send message.
            # Look for the response
            amount_received = 0
            amount_expected = len(message)

            # TODO: We need to alter this so we just send back a confirmation, not all data.
            while amount_received < amount_expected:  # Loop until expected data is recieved.
                data = sock.recv(4096)  # Break data into chunks.
                amount_received += len(data)  # Count collected data.
            self.address = tuple(server_address)
        finally:
            sock.close()  # Close socket.
        return self

    def test(self):
        """
        Tests the tcpclient.

        :return: Nothing.
        """
        message = {
            'SENDER': self.settings.StageID,
            # 'DATA': bytes(open_file("stage/tests/transmit.log"), "utf8")
            'DATA': bytes('Some data here 2', "utf8")
        }
        self.tcpclient(message)


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
