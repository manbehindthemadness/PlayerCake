"""
This is our top-level ux file

This is the main program loop for the user interface.

Tips for messed up X: https://www.ibm.com/support/pages/x11-forwarding-ssh-connection-rejected-because-wrong-authentication
NOTE: Copy the .Xauthority file from root to pi.

NOTE: THE X-SERVER MUST BE RUNNING!

Good REf: https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
"""
import tkinter as tk
from tkinter import *
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

p2 = None


class Page(Frame):

    """
    Base page.
    """
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

    def show(self):
        """
        This will lift us into view
        """
        self.lift()


class Home(Frame):
    """
    This is the homepage of the writer interface
    """
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.base = Frame(
            self,
            bg=theme['main']
        )
        self.base.place(  # This is only a placeholder so we can copy and play in another file.
            x=0,
            y=0,
            width=scr_x,
            height=scr_y
        )
        self.logo_frame = Frame(  # Setup logo frame.
            self.base,
            bg=theme["main"]
        )
        self.logo_frame.place(  # Place logo frame.
            x=cp(scr_x / 2, prx(30)),
            y=pry(10),
            width=prx(30),
            height=pry(15)
        )
        self.logo = PhotoImage(file=img('playercake_logo.png', 30, 15))  # Setup main logo.
        self.logo_image = Label(  # Populate image.
            self.logo_frame,
            image=self.logo,
            bg=theme['main']
        )
        self.logo_image.image = self.logo  # Create persistent image ref cause of the gc.
        self.logo_image.pack()  # Pack it onto the frame.

        self.entry_frame = Frame(  # Setup entry button frame.
            self.base,
            bg=theme['main'],
        )
        self.entry_frame.place(  # Place entry button frame.
            x=cp(prx(50), prx(60)),
            y=cp(pry(45), pry(25)),
            width=prx(60),
            height=pry(25)
        )

        self.writer_entry_button = self.entry_button('writer.png', command=lambda: controller.show_frame("Page2"))  # Place entry buttons.
        self.audience_entry_button = self.entry_button('audience.png')
        self.writer_entry_button.grid(row=0, column=0, sticky=W)
        self.entry_spacer = Frame(
            self.entry_frame,
            bg=theme['main'],
            width=prx(9)
        )
        self.entry_spacer.grid(row=0, column=1)
        self.audience_entry_button.grid(row=0, column=2, sticky=E)

        self.power_frame = Frame(  # Setup power button frame.
            self.base,
            bg=theme['main'],
            width=prx(30),
            height=pry(10)
        )
        self.power_frame.place(  # Place power frame.
            x=cp(prx(50), prx(30)),
            y=pry(75)
        )
        self.shutdown_button = self.power_button('shutdown.png')
        self.shutdown_button.grid(row=0, column=0, sticky=W)
        self.restart_system_button = self.power_button('restart_system.png')
        self.restart_system_button.grid(row=0, column=1)
        self.restart_button = self.power_button('restart.png')
        self.restart_button.grid(row=0, column=2, sticky=E)

    def entry_button(self, image, command=None):
        """
        Creates the application launch buttons.
        """

        entry_image = PhotoImage(file=img(image, 25, 25))
        entry_button = Button(self.entry_frame, image=entry_image, command=command)
        entry_button.image = entry_image
        entry_button.configure(
            width=prx(25),
            height=pry(25),
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
        power_image = PhotoImage(file=img(image, 10, 10))
        power_button = Button(self.power_frame, image=power_image)
        power_button.image = power_image
        power_button.configure(
            width=prx(10),
            height=pry(10),
            activebackground=theme['main'],
            activeforeground=theme['main'],
            foreground=theme['main'],
            background=theme['main'],
            borderwidth=0,
            highlightthickness=0,
            relief=FLAT
        )
        return power_button


class Writer(Frame):
    """
    Writer Page.
    """
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.base = Frame(
            self,
            bg=theme['main']
        )
        self.base.place(
            x=0,
            y=0,
            width=scr_x,
            height=scr_y
        )
        self.logo_frame = Frame(
            bg=theme["main"]
        )
        self.logo_frame.place(
            x=cp(scr_x / 2, prx(30)),
            y=pry(10),
            width=prx(30),
            height=pry(15)
        )
        logo = PhotoImage(file=img('playercake_logo.png', 30, 15))  # Setup main logo.
        logo_image = Label(
            self.logo_frame,
            image=logo,
            bg=theme["main"]
        )
        logo_image.image = logo
        logo_image.pack()


class Audience(Frame):
    """
    Audience page.
    """
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 3")
        label.pack(side="top", fill="both", expand=True)


class MainView(tk.Tk):
    """
    Main application root.
    """
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)
        container.place(
            x=0,
            y=0,
            width=scr_x,
            height=scr_y
        )
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = dict()
        for F in (Home, Writer, Audience):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        # home.show()
        self.show_frame('Home')

    def show_frame(self, page_name):
        """
        Shows a frame...
        """
        frame = self.frames[page_name]
        frame.tkraise()


def open_window(parent):
    """
    This opens a new window.
    """
    return Toplevel(parent)


def cp(value, offset):
    """
    This offsets the position of an object from the the side to the middle.
    """
    return value - (offset / 2)


def prx(percent):
    """
    This ficures a percentage of x.
    """
    return percent_of(percent, scr_x)


def pry(percent):
    """
    This figures a percentage of y.
    """
    return percent_of(percent, scr_y)


def prix(percent):
    """
    This figures what percentage in x.
    """
    return percent_in(percent, scr_x)


def priy(percent):
    """
    This figures what percentage in x.

    """
    return percent_in(percent, scr_y)


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


app = MainView()
app.geometry(
    str(scr_x) + 'x' + str(scr_y) + '+0+0'
)
app.mainloop()
