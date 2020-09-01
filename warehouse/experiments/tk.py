"""
This is our top-level ux file

This is the main program loop for the user interface.

Tips for messed up X: https://www.ibm.com/support/pages/x11-forwarding-ssh-connection-rejected-because-wrong-authentication
NOTE: Copy the .Xauthority file from root to pi.

NOTE: THE X-SERVER MUST BE RUNNING!

"""

from tkinter import *
# from tkinter import ttk
from warehouse.system import system_command
from warehouse.utils import percent_of, percent_in, file_rename, image_resize
import settings
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

        self.root = Tk()
        self.root.title("PlayerCake")
        self.root.geometry(str(scr_x) + 'x' + str(scr_y) + '+0+0')
        self.root.configure(background=theme['main'])

        #  #########
        #  Home page
        #  #########

        logo = PhotoImage(file=self.img('playercake_logo.png', 30, 15))  # Setup main logo.
        logo_image = Label(
            image=logo,
            bg=theme['main']
        )
        logo_image.place(
            x=self.cp(scr_x / 2, self.prx(30)),
            y=self.pry(10),
            width=self.prx(30),
            height=self.pry(15)
        )

        self.entry_frame = Frame(
            self.root,
            bg=theme['main'],
        )
        self.entry_frame.place(  # Create entry button container.
            x=self.cp(self.prx(50), self.prx(60)),
            y=self.cp(self.pry(45), self.pry(25)),
            width=self.prx(60),
            height=self.pry(25)
        )

        self.writer_entry_button = self.entry_button('writer.png')  # Place entry buttons.
        self.audience_entry_button = self.entry_button('audience.png')
        self.writer_entry_button.grid(row=0, column=0, sticky=W)
        self.entry_spacer = Frame(
            self.entry_frame,
            bg=theme['main'],
            width=self.prx(9)
        )
        self.entry_spacer.grid(row=0, column=1)
        self.audience_entry_button.grid(row=0, column=2, sticky=E)

        self.power_frame = Frame(
            self.root,
            bg=theme['main'],
            width=self.prx(30),
            height=self.pry(10)
        )
        self.power_frame.place(
            x=self.cp(self.prx(50), self.prx(30)),
            y=self.pry(75)
        )
        self.shutdown_button = self.power_button('shutdown.png')
        self.shutdown_button.grid(row=0, column=0, sticky=W)
        self.restart_system_button = self.power_button('restart_system.png')
        self.restart_system_button.grid(row=0, column=1)
        self.restart_button = self.power_button('restart.png')
        self.restart_button.grid(row=0, column=2, sticky=E)

        self.root.mainloop()

    def entry_button(self, image, command=''):
        """
        Creates the application launch buttons.
        """

        entry_image = PhotoImage(file=self.img(image, 25, 25))
        entry_button = Button(self.entry_frame, image=entry_image, command=command)
        entry_button.image = entry_image
        entry_button.configure(
            width=self.prx(25),
            height=self.pry(25),
            activebackground=theme['main'],
            activeforeground=theme['main'],
            foreground=theme['main'],
            background=theme['main'],
            borderwidth=0,
            highlightthickness=0,
            relief=FLAT
        )
        # entry_button.pack(anchor=NW)
        return entry_button

    def power_button(self, image):
        """
        This creates the power buttons on the home page.
        """
        power_image = PhotoImage(file=self.img(image, 10, 10))
        power_button = Button(self.power_frame, image=power_image)
        power_button.image = power_image
        power_button.configure(
            width=self.prx(10),
            height=self.pry(10),
            activebackground=theme['main'],
            activeforeground=theme['main'],
            foreground=theme['main'],
            background=theme['main'],
            borderwidth=0,
            highlightthickness=0,
            relief=FLAT
        )
        return power_button

    @staticmethod
    def open_window(parent):
        """
        This opens a new window.
        """
        window = Toplevel(parent)

    @staticmethod
    def cp(value, offset):
        """
        This offsets the position of an object from the the side to the middle.
        """
        return value - (offset / 2)

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
    def prix(percent):
        """
        This figures what percentage in x.
        """
        return percent_in(percent, scr_x)

    @staticmethod
    def priy(percent):
        """
        This figures what percentage in x.

        """
        return percent_in(percent, scr_y)

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


UX()
