"""
This is the main program loop for the writer application.

Tops for messed up X: https://www.ibm.com/support/pages/x11-forwarding-ssh-connection-rejected-because-wrong-authentication

NOTE: THE X-SERVER MUST BE RUNNING!
"""

from guizero import App, Box, Text
from warehouse.system import system_command
from warehouse import settings
import os

scr_x, scr_y = settings.screensize

os.environ['DISPLAY'] = 'localhost:11.0'
system_command(['/usr/bin/xhost', '+'])

app = App()
box = Box(app, width=150, height=150)
box.bg = "red"
box.border = True

text = Text(box, text="hello")
app.display()
