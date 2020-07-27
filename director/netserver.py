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


def udpserver():
    """
    Launches a UDP announce server.
    :return: Nothing.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    # server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Enable broadcasting mode
    # server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    server.bind((settings.BindAddr, 37020))  # This is a windows thing...

    server.settimeout(0.2)
    statement = 'director:' + socket.gethostname() + ':' + settings.DirectorID + ':' + settings.BindAddr + ':' + str(settings.TCPBindPort)
    message = bytes(statement, "utf8")
    while True:
        server.sendto(message, ("<broadcast>", 37020))
        print("message sent!")
        time.sleep(1)
    # server.sendto(message, ("<broadcast>", 37020))
    # print("message sent!")


def tcpserver():
    """
    Launches a TCP communication server.
    :return: Nothing.
    """
    announcethread = Thread(target=udpserver, args=())
    announcethread.start()
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (settings.BindAddr, settings.TCPBindPort)
    print(sys.stderr, 'starting up on %s port %s' % server_address)
    sock.bind(server_address)
    # Listen for incoming connections
    sock.listen(1)

    while True:
        # Wait for a connection
        print(sys.stderr, 'waiting for a connection')
        connection, client_address = sock.accept()  # This waits until a client connects.
        try:
            print(sys.stderr, 'connection from', client_address)

            # Receive the data in small chunks and retransmit it
            while True:
                data = connection.recv(16)
                print(sys.stderr, 'received "%s"' % data)
                if data:
                    print(sys.stderr, 'sending data back to the client')
                    connection.sendall(data)
                else:
                    print(sys.stderr, 'no more data from', client_address)
                    break

        finally:
            # Clean up the connection
            connection.close()
        announcethread.join()
