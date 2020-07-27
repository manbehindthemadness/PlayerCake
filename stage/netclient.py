"""
This is the network client file, It includes both UDP and TCP clients.
Reference: https://github.com/ninedraft/python-udp/blob/master/client.py
"""

import socket
import sys
from director import settings


def udpclient():
    """
    Launches a UDP listener.
    :return: Upstream server connection string.
    :rtype: list
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP

    # client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Enable broadcasting mode
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    client.bind(("", 37020))
    search = True
    server_info = None
    while search:
        data, addr = client.recvfrom(1024)
        if settings.DirectorID in str(data):
            print("received message: %s" % data)
            server_info = data.decode("utf8").split(':')
            search = False
    return server_info


def tcpclient():
    """
    Launches a TCP client.
    :return: Nothing.
    """
    server_info = None
    while not server_info:
        server_info = udpclient()  # Look for upstream server.
        print('searching for Director...')
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    print(server_info[3], int(server_info[4]))
    server_address = (server_info[3], int(server_info[4]))
    print(sys.stderr, 'connecting to %s port %s' % server_address)
    sock.connect(server_address)
    try:

        # Send data
        message = b'This is the message.  It will be repeated.'
        print(sys.stderr, 'sending "%s"' % message)
        sock.sendall(message)

        # Look for the response
        amount_received = 0
        amount_expected = len(message)

        while amount_received < amount_expected:
            data = sock.recv(16)
            amount_received += len(data)
            print(sys.stderr, 'received "%s"' % data)

    finally:
        print(sys.stderr, 'closing socket')
        sock.close()
