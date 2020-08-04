"""
This is where we are going to store all of our communication related code.
"""

import socket
import time
import sys
from threading import Thread
from director import settings  # TODO: We need to figure a way to pass this into the classes instead of directly importing.
from warehouse.loggers import dprint


term = False


class NetServer:
    """
    This is the network server module, it contains both TCP and UDP servers.
    Reference:
        https://github.com/ninedraft/python-udp/blob/master/client.py
        https://stackoverflow.com/questions/43475468/windows-python-udp-broadcast-blocked-no-firewall
    """

    @staticmethod
    def udpserver():
        """
        Launches a UDP announce server.
        :return: Nothing.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create UDP transmission socket.
        if settings.Envirnment == 'pure':
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        elif settings.Envirnment == 'mixed':  # This is a windows thing...
            server.bind((settings.BindAddr, 37020))
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

        server.settimeout(0.2)  # Define server timeout.
        statement = 'director:' + socket.gethostname() + ':' + settings.DirectorID + ':' + settings.BindAddr + ':' + str(settings.TCPBindPort)  # Define data package.
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
        server_address = (settings.BindAddr, settings.TCPBindPort)  # Create connection string.
        dprint(settings, ('starting up on %s port %s' % server_address,))
        sock.bind(server_address)  # Bind connection string to socket.
        sock.listen(1)  # Listen for incoming connections.

        while True:
            output = b''
            dprint(settings, (sys.stderr, 'waiting for a connection',))
            connection, client_address = sock.accept()  # This waits until a client connects.
            try:
                dprint(settings, ('connection from', client_address,))

                while True:  # Receive the data in small chunks and retransmit it
                    data = connection.recv(4096)
                    output += data
                    # print(sys.stderr, 'received "%s"' % data)
                    if data:
                        # print(sys.stderr, 'sending data back to the client')
                        connection.sendall(data)
                    else:
                        dprint(settings, (output,))
                        dprint(settings, ('no more data from', client_address,))
                        break
            finally:
                connection.close()  # Clean up the connection.
                term = False  # Close transmitter thread.


class NetClient:
    """
    This is a network client connector.

    """

    @staticmethod
    def open_file(filename):
        """
        Opens a text file.
        :param filename: File to open.
        :type filename: Str
        :return: Contents of file.
        :rtype: str
        """
        file = open(filename)
        return file.read()

    @staticmethod
    def udpclient(_settings):
        """
        Launches a UDP listener.

        :param _settings: Instance of settings file.
        :type _settings: module
        :return: Upstream server connection string.
        :rtype: list
        """
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create UDP client socket.
        if settings.Envirnment == 'pure':
            client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Specify socket options.
            client.bind(("", 37020))  # Bind the socket to all adaptors and the target port.
        elif settings.Envirnment == 'mixed':
            client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Windows compatable version.
            client.bind(("", 37020))  # Bind the socket to all adaptors and the target port.
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

        search = True
        server_info = None
        while search:  # Listen for upstream server to identify itself.
            data, addr = client.recvfrom(1024)
            if _settings.DirectorID in str(data):  # TODO: revise for cross-application compatibility.
                dprint(settings, ("received message: %s" % data,))
                server_info = data.decode("utf8").split(':')
                search = False
        return server_info  # Return upstream server TCP connection information.

    def tcpclient(self, _settings, message):
        """
        Launches a TCP client.

        TODO: Find a way to cache the upstream server info.

        :param _settings: Instance of settings file.
        :type _settings: module
        :param message: Data to transmit
        :type message: bytes
        :return: Nothing.
        """
        server_info = None
        while not server_info:  # Look for upstream server.
            server_info = self.udpclient(_settings)
            dprint(settings, ('searching for Director...',))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.

        # print(server_info[3], int(server_info[4]))
        server_address = (server_info[3], int(server_info[4]))  # Collect server connection string.
        dprint(_settings, ('connecting to %s port %s' % server_address,))
        sock.connect(server_address)  # Connect the socket to the port where the server is listening.
        try:
            # print(sys.stderr, 'sending "%s"' % message)
            sock.sendall(message)  # Send message.

            # Look for the response
            amount_received = 0
            amount_expected = len(message)

            while amount_received < amount_expected:  # Loop until expected data is recieved.
                data = sock.recv(4096)  # Break data into chunks.
                amount_received += len(data)  # Count collected data.
                # print(sys.stderr, 'received "%s"' % data)

        finally:
            dprint(_settings, ('closing socket',))
            sock.close()  # Close socket.

    def test(self, _settings):
        """
        Tests the tcpclient.

        :param _settings: Instance of configuration file.
        :type _settings: Module
        :return: Nothing.
        """
        self.tcpclient(_settings, bytes(self.open_file("stage/tests/transmit.log"), "utf8"))
