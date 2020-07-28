"""
This is the network server module, it contains both TCP and UDP servers.
Reference:
    https://github.com/ninedraft/python-udp/blob/master/client.py
    https://stackoverflow.com/questions/43475468/windows-python-udp-broadcast-blocked-no-firewall
"""
import socket
import time
import sys
from threading import Thread
from director import settings
from warehouse.loggers import dprint


term = False


def udpserver():
    """
    Launches a UDP announce server.
    :return: Nothing.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create UDP transmission socket.
    if settings.Envirnment == 'pure':
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    elif settings.Envirnment == 'mixed': # This is a windows thing...
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


def tcpserver():
    """
    Launches a TCP communication server.
    :return: Nothing.
    """
    global term
    announcethread = Thread(target=udpserver, args=())  # Create transmitter thread.
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
