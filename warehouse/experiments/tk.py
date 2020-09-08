"""
Tkinter playground...
"""
import os
import random
import tkinter as tk
from tkinter.font import Font

import pyqrcode
from pyqrcode import QRCode
import png
from PIL import Image, ImageTk

from warehouse.system import system_command

os.environ['DISPLAY'] = 'localhost:11.0'
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])
display = system_command(['echo', '$DISPLAY'])
print(display)


class QRCodeLabel(tk.Label):
    def __init__(self, parent):
        super().__init__(parent)
        s = "www.geeksforgeeks.org"
        url = pyqrcode.create(s)
        url.png('myqr.png', scale=8)
        self.image = tk.PhotoImage(file='myqr.png')
        self.x = self.image.width()
        self.y = self.image.height()
        self.configure(
            image=self.image
        )


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.label = QRCodeLabel(self)
        self.label.pack()


if __name__ == "__main__":
    App().mainloop()
