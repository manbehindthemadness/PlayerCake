"""
This is the software configuration settings file. These values are general defaults and should be modified in the logal_settings file not here!
"""
Debug = True  # Enables debugging
Debug_Pretty = False  # Pprint the debug info instead of print. - Disables Debug_filter.
Debug_Update_Only = True # Only update the debug model with new data and ignotr empty ones - Useful for catching fast operations.
Debug_Filter = [  # This lists the includes from the real time data model that will be returned to console.
    'LISTENER',
    'ADDRESSES',
]
DirectorID = '6efc1846-d015-11ea-87d0-0242ac130003'  # This ID matches Stage clients to their respective Directors.
Envirnment = 'mixed'  # Mixed means that we are using windows or apple to communicate with Stage: mixed/pure
BindAdaptor = 'Eth2-SmtSw'  # This is the network adaptor used to handle incoming and outgoing network traffic.
TCPBindPort = 12000  # TCP Listener Port.
UDPBindPort = 37020  # UDP Listener Port.
UDPBroadcastPort = 37020  # Port to broadcast on.
NetworkTimeout = 5  # This is the connection timeout for the network sockets.
Environment = 'mixed'
Role = 'director'  # This is the role announcement that is used by the network client UDP lookup broadcast.
Target = 'stage'  # This is the up-stream role used to direct rebort connections.
Paired_Stages = [  # This identifies the stages that have been paired to this director. (This will be automatic once we have QR code functionality in place).
    'a9b3cfb3-c72d-4efd-993d-6c8dccbb8609',
]

# Timings:

Debug_Cycle = 2  # Number in seconds to update the debug logs.
