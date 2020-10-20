"""
This is the main program loop for the writer application.

Tops for messed up X: https://www.ibm.com/support/pages/x11-forwarding-ssh-connection-rejected-because-wrong-authentication
NOTE: Copy the .Xauthority file from root to pi.

NOTE: THE X-SERVER MUST BE RUNNING!
"""

from tkinter import *
from tkinter import ttk
from warehouse.system import system_command
from warehouse.utils import file_rename
from warehouse.uxutils import image_resize
from warehouse.math import percent_of  # , percent_in
from writer import settings
import os

scr_x, scr_y = settings.screensize

theme = settings.themes[settings.theme]

# This crap is for tunneling the app over ssh
os.environ['DISPLAY'] = settings.display
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])


class UX:
    """
    This is our user interface class
    """

    def __init__(self):
        root = Tk()
        root.title("PlayerCake")

        canvas = Canvas(root, width=scr_x, height=scr_y)
        canvas.config(
            bg=theme['main']
        )
        canvas.pack()

        button_style = ttk.Style()  # This is the magic right here.
        button_style.configure(
            "b1.TButton",
            borderwidth=0,
            background=theme['main']
        )

        logo = PhotoImage(file=self.img('playercake_logo.png', 30, 15))
        # logo = PhotoImage(file='/home/pi/playercake/img/resize/dark_playercake_logo308_116.png')
        canvas.create_image(self.prx(30), self.pry(15), image=logo, anchor=NW)

        writer_entry_image = PhotoImage(file=self.img('writer.png', 25, 25))
        writer_entry_button = Button(root, image=writer_entry_image, anchor=W)
        # writer_entry_button.image = writer_entry_image
        writer_entry_button.configure(
            width=self.prx(25),
            height=self.pry(25),
            activebackground=theme['main'],
            # activeforeground=theme['main'],
            # foreground=theme['main'],
            background=theme['main'],
            # borderwidth=0,
            highlightthickness=0,
            relief=FLAT
        )
        writer_entry_button.pack()
        canvas.create_window(self.prx(25), self.pry(25), anchor=NW, window=writer_entry_button)

        root.mainloop()

    @staticmethod
    def prx(percent):
        """
        This ficures a percentage of x.
        """
        return percent_of(percent, scr_x)

    @staticmethod
    def pry(percent):
        """
        This figures a percentage of y.
        """
        return percent_of(percent, scr_y)

    @staticmethod
    def img(image, x_percent, y_percent, aspect=True):
        """
        Quick and dirty way to grab images.
        """
        image = file_rename(settings.theme + '_', image, reverse=True)
        image = image_resize(
                scr_x,
                scr_y,
                image,
                x_percent,
                y_percent,
                aspect
            )
        return image
