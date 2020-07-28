"""
This is the network client file, It includes both UDP and TCP clients.
Reference: https://github.com/ninedraft/python-udp/blob/master/client.py
"""

import socket
import sys
from director import settings


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


def udpclient():
    """
    Launches a UDP listener.
    :return: Upstream server connection string.
    :rtype: list
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create UDP client socket.

    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Specify socket options.
    # client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Windows compatable version.

    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting mode.

    client.bind(("", 37020))  # Bind the socket to all adaptors and the target port.
    search = True
    server_info = None
    while search:  # Listen for upstream server to identify itself.
        data, addr = client.recvfrom(1024)
        if settings.DirectorID in str(data):
            print("received message: %s" % data)
            server_info = data.decode("utf8").split(':')
            search = False
    return server_info  # Return upstream server TCP connection information.


def tcpclient():
    """
    Launches a TCP client.

    TODO: Find a way to cache the upstream server info.

    :return: Nothing.
    """
    server_info = None
    while not server_info:  # Look for upstream server.
        server_info = udpclient()
        print('searching for Director...')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket.

    print(server_info[3], int(server_info[4]))
    server_address = (server_info[3], int(server_info[4]))  # Collect server connection string.
    print(sys.stderr, 'connecting to %s port %s' % server_address)
    sock.connect(server_address)  # Connect the socket to the port where the server is listening.
    try:

        # Send data
        # message = b'This is the message.  It will be repeated.'  # Define message.
        message = bytes(open_file("stage/tests/transmit.log"), "utf8")
        print(sys.stderr, 'sending "%s"' % message)
        sock.sendall(message)  # Send message.

        # Look for the response
        amount_received = 0
        amount_expected = len(message)

        while amount_received < amount_expected:  # Loop until expected data is recieved.
            data = sock.recv(4096)  # Break data into 16 bit chunks.
            amount_received += len(data)  # Count collected data.
            print(sys.stderr, 'received "%s"' % data)

    finally:
        print(sys.stderr, 'closing socket')
        sock.close()  # Close socket.
