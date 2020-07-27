"""
This is the network server module, it contains both TCP and UDP servers.
Reference:
    https://github.com/ninedraft/python-udp/blob/master/client.py
    https://stackoverflow.com/questions/43475468/windows-python-udp-broadcast-blocked-no-firewall
"""
import socket
import time
from director import settings

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Thanks to @stevenreddie
# server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Enable broadcasting mode
# server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

server.bind((settings.BindAddr, 37020))  # This is a windows thing...

# Set a timeout so the socket does not block
# indefinitely when trying to receive data.
server.settimeout(0.2)
message = b"your very important message"
while True:
    server.sendto(message, ("<broadcast>", 37020))
    print("message sent!")
    time.sleep(1)
