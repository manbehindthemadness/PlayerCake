"""
This is the network client file, It includes both UDP and TCP clients.
Reference: https://github.com/ninedraft/python-udp/blob/master/client.py
"""

import socket
# import sys
from director import settings as _settings
from warehouse.loggers import dprint


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


def udpclient(settings):
    """
    Launches a UDP listener.

    :param settings: Instance of settings file.
    :type settings: module
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
        if settings.DirectorID in str(data):
            dprint(settings, ("received message: %s" % data,))
            server_info = data.decode("utf8").split(':')
            search = False
    return server_info  # Return upstream server TCP connection information.


def tcpclient(settings, message):
    """
    Launches a TCP client.

    TODO: Find a way to cache the upstream server info.

    :param settings: Instance of settings file.
    :type settings: module
    :param message: Data to transmit
    :type message: bytes
    :return: Nothing.
    """
    server_info = None
    while not server_info:  # Look for upstream server.
        server_info = udpclient(settings)
        dprint(settings, ('searching for Director...',))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.

    # print(server_info[3], int(server_info[4]))
    server_address = (server_info[3], int(server_info[4]))  # Collect server connection string.
    dprint(settings, ('connecting to %s port %s' % server_address,))
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
        dprint(settings, ('closing socket',))
        sock.close()  # Close socket.


def test():
    """
    Tests the tcpclient.
    :return:
    """
    tcpclient(_settings, bytes(open_file("stage/tests/transmit.log"), "utf8"))
