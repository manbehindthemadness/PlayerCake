"""
This is the main program loop for the writer application.

Tops for messed up X: https://www.ibm.com/support/pages/x11-forwarding-ssh-connection-rejected-because-wrong-authentication
"""

from guizero import App, Box, Text
from warehouse.system import system_command
import os

os.environ['DISPLAY'] = 'localhost:11.0'
system_command(['/usr/bin/xhost', '+'])

app = App()
box = Box(app, width=150, height=150)
box.bg = "red"
box.border = True

text = Text(box, text="hello")
app.display()