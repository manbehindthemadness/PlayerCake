"""
Holding place for TKInter experiments.
"""

from tkinter import *
from tkinter import ttk, PhotoImage
from warehouse.system import system_command
from warehouse.utils import percent_of, percent_in, file_rename, image_resize
from writer import settings
import os

scr_x, scr_y = settings.screensize

# This crap is for tunneling the app over ssh
os.environ['DISPLAY'] = 'localhost:11.0'
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])


def img(image, x_percent, y_percent, aspect=True):
    """
    Quick and dirty way to grab images.
    """
    image = file_rename(settings.theme + '_', image, reverse=True)
    return PhotoImage(
        image_resize(
            scr_x,
            scr_y,
            image,
            x_percent,
            y_percent,
            aspect
        )
    )


def calculate(*args):
    """something"""
    try:
        value = float(feet.get())
        meters.set(int(0.3048 * value * 10000.0 + 0.5)/10000.0)
    except ValueError:
        pass

root = Tk()
root.title("PlayerCake")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=3, row=3)
# root.columnconfigure(0, weight=1)
# root.rowconfigure(0, weight=1)

feet = StringVar()
meters = StringVar()

feet_entry = ttk.Entry(mainframe, width=7, textvariable=feet)
feet_entry.grid(column=2, row=1, sticky=(W, E))

button_style = ttk.Style()  # This is the magic right here.
button_style.configure("b1.TButton", borderwidth=0)


ttk.Label(mainframe, textvariable=meters).grid(column=2, row=2, sticky=(W, E))
ttk.Button(mainframe, text="Calculate", command=calculate, style='b1.TButton').grid(column=3, row=3, sticky=W)

ttk.Label(mainframe, text="feet").grid(column=3, row=1, sticky=W)
ttk.Label(mainframe, text="is equivalent to").grid(column=1, row=2, sticky=E)
ttk.Label(mainframe, text="meters").grid(column=3, row=2, sticky=W)

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

feet_entry.focus()
root.bind('<Return>', calculate)

root.mainloop()
