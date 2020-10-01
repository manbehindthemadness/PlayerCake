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
from warehouse.system import system_command
from warehouse.loggers import dprint


class NetCom:
    """
    This is the network server module, it contains both TCP and UDP servers.
    Reference:
        https://github.com/ninedraft/python-udp/blob/master/client.py
        https://stackoverflow.com/questions/43475468/windows-python-udp-broadcast-blocked-no-firewall
    """
    def __init__(self, controller):
        self.controller = controller
        self.reconnecting = self.controller.reconnecting
        self.term = False
        self.address = None
        self.message = None
        self.settings = self.controller.settings
        self.types = (bytes, bytearray)
        self.data = bytes()
        self.output = None
        # print('connecting wireless')
        #
        self.bindaddr = GetIP(self.settings).ipv4
        ret = 0
        while not self.bindaddr:
            self.bindaddr = GetIP(self.settings).ipv4
            ret += 1
            if ret > 10:
                self.bindaddr = self.settings.bindaddr
        print('opening listening ports')
        system_command(['firewall-cmd', '--zone=public', '--add-port=' + str(self.settings.tcpbindport) + '/tcp'])
        system_command(['firewall-cmd', '--zone=public', '--add-port=' + str(self.settings.udpbindport) + '/udp'])

        announcethread = Thread(target=self.udpserver, args=())  # Create transmitter thread.
        announcethread.start()  # Launch UDP transmitter.

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        self.server_address = (self.bindaddr, self.settings.tcpbindport)  # Create connection string.
        dprint(self.settings, ('starting up on %s port %s' % self.server_address,))
        self.sock.bind(self.server_address)  # Bind connection string to socket.
        self.sock.listen(1)  # Listen for incoming connections.
        self.udpsock = None
        self.client_address = None
        self.connection = None

    def reconnect(self):
        """
        This restarts the networking services in the event we have a bad wifi connection.
        """
        if not self.reconnecting:
            self.reconnecting = True
            print('network dropout detected, reconnecting')
            time.sleep(5)
            if self.settings.role == 'stage':
                self.controller.lines.append('wifi reset')
            system_command(['service', 'networking', 'restart'])
            time.sleep(2)
            system_command(['service', 'wpa_supplicant', 'restart'])
            time.sleep(2)
            system_command(
                ['wpa_supplicant', '-B', '-i ' + self.settings.bindadaptor, '/etc/wpa_supplicant/wpa_supplicant.conf',
                 '-D wext'])
            time.sleep(5)
            self.reconnecting = False

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
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

        server.settimeout(0.2)  # Define server timeout.
        # print(self.settings.role, socket.gethostname(), self.settings.director_id, self.bindaddr, str(self.settings.tcpbindport))
        statement = self.settings.role + ':' + socket.gethostname() + ':' + self.settings.director_id + ':' + self.bindaddr + ':' + str(self.settings.tcpbindport)  # Define data package.
        # TODO: Encode the above information.
        message = self.encode(statement).message
        while not self.term:  # Broadcast until termination signal is recieved.
            server.sendto(message, ("<broadcast>", self.settings.udpbroadcastport))  # Send message.
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
                # self.connection, self.client_address = self.sock.accept()  # This waits until a client connects.
                self.data = self.connection.recv(4096)  # TODO: We need to alter this so we just send back a confirmation, not all data.
                self.output += self.data
                if self.data:
                    self.connection.sendall(self.data)
                else:
                    try:
                        self.output = self.decode(self.output).message
                    except CBORDecodeEOF:
                        dprint(self.settings, ('Invalid connection data, CBOR EOF, aborting',))
                    # self.connection.close()  # Clean up the connection.
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
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Specify socket options.
        client.bind(("", self.settings.udpbindport))  # Bind the socket to all adaptors and the target port..
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

        search = True
        while search:  # Listen for upstream server to identify itself.
            data, addr = client.recvfrom(1024)
            self.data = self.decode(data).message.split(':')
            if self.data[0] == self.settings.target and self.data[2] == self.settings.director_id:  # TODO: revise for cross-application compatibility.
                search = False
        return self.data  # Return upstream server TCP connection information.

    def tcpclient(self, message_enc, address=None, fail=0):
        """
        Launches a TCP client.

        TODO: Find a way to cache the upstream server info.

        :param message_enc: Data to transmit
        :type message_enc:
        :param address: Optional server address and port: 1.2.3.4:5.
        ::type address: str
        :param fail:  This is a reconnect failure count, it will allow us to trigger additional measures for reconnect.
        :type fail: int
        :return: Self.
        """
        message = self.encode(message_enc).message
        # dprint(self.settings, ('connection init',))
        server_info = None
        if address:  # Use server address where able.
            server_info = address.split(':')
        while not server_info:  # Look for upstream server.
            dprint(self.settings, ('searching for connection...',))
            server_info = self.udpclient()
        # dprint(self.settings, ('connection found:', server_info))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.
        sock.settimeout(self.settings.networktimeout)
        if address:
            server_address = server_info[0], int(server_info[1])
        else:
            server_address = (server_info[3], int(server_info[4]))  # Collect server connection string.
        # print('connecting to %s port %s' % server_address,)
        try:
            sock.connect(server_address)  # Connect the socket to the port where the server is listening.
        except OSError as err:
            print('connection failed, retrying', err)
            time.sleep(1)
            fail += 1
            sock.close()  # Close socket.
            self.tcpclient(message_enc, address, fail)  # Retry connection.

        try:
            sock.sendall(message)  # Send message.
            # Look for the response
            amount_received = 0
            amount_expected = len(message)
            while amount_received < amount_expected:  # Loop until expected data is recieved.
                data = sock.recv(4096)  # Break data into chunks.
                amount_received += len(data)  # Count collected data.
            self.address = tuple(server_address)
        except (BrokenPipeError, OSError) as err:
            print('connection failed, broken pipe, retrying', err)
            time.sleep(1)
            fail += 1
            sock.close()  # Close socket.
            self.tcpclient(message_enc, address, fail)  # Retry connection.
        finally:
            sock.close()  # Close socket.
        return self

    # def tcpclient(self, message, address=None, fail=0):
    #     """
    #     Launches a TCP client.
    #
    #     TODO: Find a way to cache the upstream server info.
    #
    #     :param message: Data to transmit
    #     :type message:
    #     :param address: Optional server address and port: 1.2.3.4:5.
    #     ::type address: str
    #     :param fail:  This is a reconnect failure count, it will allow us to trigger additional measures for reconnect.
    #     :type fail: int
    #     :return: Self.
    #     """
    #     # dprint(self.settings, ('connection init',))
    #     server_info = None
    #     if address:  # Use server address where able.
    #         server_info = address.split(':')
    #     while not server_info:  # Look for upstream server.
    #         dprint(self.settings, ('searching for connection...',))
    #         server_info = self.udpclient()
    #     # dprint(self.settings, ('connection found:', server_info))
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.
    #     sock.settimeout(self.settings.networktimeout)
    #     if address:
    #         server_address = server_info[0], int(server_info[1])
    #     else:
    #         server_address = (server_info[3], int(server_info[4]))  # Collect server connection string.
    #     # print('connecting to %s port %s' % server_address,)
    #     try:
    #         sock.connect(server_address)  # Connect the socket to the port where the server is listening.
    #     except OSError as err:
    #         print('connection failed, retrying', err)
    #         time.sleep(1)
    #         fail += 1
    #         sock.close()  # Close socket.
    #         self.tcpclient(message, address, fail)  # Retry connection.
    #     message = self.encode(message).message
    #     try:
    #         sock.sendall(message)  # Send message.
    #         # Look for the response
    #         amount_received = 0
    #         amount_expected = len(message)
    #         while amount_received < amount_expected:  # Loop until expected data is recieved.
    #             data = sock.recv(4096)  # Break data into chunks.
    #             amount_received += len(data)  # Count collected data.
    #         self.address = tuple(server_address)
    #     except (BrokenPipeError, OSError):
    #         print('connection failed, broken pipe, retrying')
    #         time.sleep(1)
    #         fail += 1
    #         sock.close()  # Close socket.
    #         self.tcpclient(message, address, fail)  # Retry connection.
    #     finally:
    #         sock.close()  # Close socket.
    #     return self

    def test(self):
        """
        Tests the tcpclient.

        :return: Nothing.
        """
        message = {
            'SENDER': self.settings.stageid,
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
            print('we have settings')
            self.adaptor = settings.bindadaptor
        if adaptor:
            self.adaptor = adaptor
        self.data = psutil.net_if_addrs()[self.adaptor]
        self.v4 = self.data[0]
        self.ipv4 = None
        for eth in self.data:
            if str(eth[0]) == 'AddressFamily.AF_INET':
                self.ipv4 = str(eth[1])
