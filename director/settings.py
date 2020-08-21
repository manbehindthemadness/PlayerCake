"""
This is the software configuration settings file. These values are general defaults and should be modified in the logal_settings file not here!
"""
Debug = True  # Enables debugging
DirectorID = '6efc1846-d015-11ea-87d0-0242ac130003'  # This ID matches Stage clients to their respective Directors.
Envirnment = 'mixed'  # Mixed means that we are using windows or apple to communicate with Stage: mixed/pure
BindAdaptor = 'Eth2-SmtSw'  # This is the network adaptor used to handle incoming and outgoing network traffic.
TCPBindPort = 12000
Environment = 'mixed'
Role = 'director' # This is the role announcement that is used by the network client UDP lookup broadcast.
Target = 'stage'  # This is the up-stream role used to direct rebort connections.
