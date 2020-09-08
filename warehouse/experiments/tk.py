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

s = "www.geeksforgeeks.org"

# Generate QR code
url = pyqrcode.create(s)

# Create and save the svg file naming "myqr.svg"
# url.svg("myqr.svg", scale=8)

# Create and save the png file naming "myqr.png"
url.png('myqr.png', scale=6)



class QRCodeLabel(tk.Label):
    def __init__(self, parent, qr_data):
        super().__init__(parent)
        print('QRCodeLabel("{}")'.format(qr_data))
        self.image = tk.PhotoImage(file='myqr.png')
        self.configure(image=self.image)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        buttonQR = tk.Button(text="Generate!", bg="white", command=self.generateQR)
        buttonQR.grid(row=2, column=0)
        self.qr_label = None


    def generateQR(self):
        if self.qr_label:
            self.qr_label.destroy()

        self.qr_label = QRCodeLabel(self, random.choice(["You Win!", "You Lose!"]))
        self.qr_label.grid(row=1, column=0, sticky="nsew")


if __name__ == "__main__":
    App().mainloop()
