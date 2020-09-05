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
from tkinter.filedialog import askopenfilename
from warehouse.system import system_command
from warehouse.utils import percent_of, percent_in, file_rename, image_resize
from writer.plot import pymesh_stl
import settings
import os

scr_x, scr_y = settings.screensize

theme = settings.themes[settings.theme]
defaults = settings.defaults

# This crap is for tunneling the app over ssh
os.environ['DISPLAY'] = settings.display
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])

rt_data = dict()


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
        global rt_data
        self.rt_data = rt_data
        self.controller = controller
        self.system_command = system_command
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

        self.writer_entry_button = self.entry_button('writer.png', command=lambda: controller.show_frame("Writer"))  # Place entry buttons.
        self.audience_entry_button = self.entry_button('audience.png', command=lambda: controller.show_frame("Audience"))
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
        self.shutdown_button = self.power_button('shutdown.png', self.shutdown_command)
        self.shutdown_button.grid(row=0, column=0, sticky=W)
        self.restart_system_button = self.power_button('restart_system.png', self.restart_system_command)
        self.restart_system_button.grid(row=0, column=1)
        self.restart_button = self.power_button('restart.png', self.restart_command)
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

    def power_button(self, image, command=None):
        """
        This creates the power buttons on the home page.
        """
        power_image = PhotoImage(file=img(image, 10, 10))
        power_button = Button(self.power_frame, image=power_image, command=command)
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

    def shutdown_command(self):
        """
        This powers off the SOC.
        """
        self.system_command(
            ['sudo', 'poweroff']
        )

    def restart_system_command(self):
        """
        This restarts the SOC.
        """
        self.system_command(
            ['sudo', 'reboot']
        )

    def restart_command(self):
        """
        This restarts the playercake service.
        """
        self.system_command(
            ['sudo', 'service', 'playercake', 'restart']
        )


class Writer(Frame):
    """
    Writer Page.
    """

    # noinspection PyShadowingNames
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        global rt_data
        self.rt_data = rt_data
        self.defaults = defaults
        for sett in self.defaults:  # Populate defaults
            self.rt_data[sett] = StringVar()
            self.rt_data[sett].set(str(defaults[sett]))
        self.rt_data['plotfile'] = str()
        self.rt_data['temp'] = dict()
        self.rt_data['0'] = StringVar()
        self.rt_data['0'].set('0')
        self.temp = self.rt_data['temp']
        self.temp['number'] = StringVar()
        self.temp['number'].set('0')

        self.controller = controller
        self.numpad = NumPad(self, self.controller)
        self.plotter = pymesh_stl
        self.number = None
        self.plot = None
        self.plotfile = None
        self.base = Frame(  # Setup base.
            self,
            bg=theme['main']
        )
        self.base.place(  # Place Base.
            x=0,
            y=0,
            width=scr_x,
            height=scr_y
        )
        #  ###########
        #  Plot window
        #  ###########
        self.plot_frame = Frame(  # Setup plotframe.
            self.base,
            bg=theme['main']
        )
        self.plot_frame.place(  # Place plotframe.
            x=cp(prx(50), scr_y),
            width=scr_y,
            height=scr_y
        )
        self.panel_size = int((scr_x - scr_y) / 2)  # Figure our panel size.
        self.left_panel_frame = Frame(  # Setup left panel.
            self.base,
            bg=theme['main']
        )
        #  ##################
        #  Left hand controls
        #  ##################
        self.left_panel_frame.place(  # Place left panel.
            x=0,
            y=0,
            width=self.panel_size,
            height=scr_y
        )
        self.back_button = self.half_button(  # Setup back button.
            self.left_panel_frame,
            'back.png',
            command=lambda: controller.show_frame("Home")
        )
        self.back_button.grid(row=0, column=0)
        self.open_button = self.half_button(  # Setup file open button.
            self.left_panel_frame,
            'open.png',
            command=self.get_plotfile
        )
        self.open_button.grid(row=0, column=1)

        render = StringVar()
        self.render_button = self.full_button(
            self.left_panel_frame,
            'fullbuttonframe.png',
            command=self.render_plotfile,
            text='audition'  # TODO: Now that we have this working we can iron out the tangle that is the weight buttons.
        )
        self.render_button.grid(row=1, columnspan=2)
        render.set('Render')

        #  ###################
        #  Right hand controls
        #  ###################
        self.right_panel_frame = Frame(  # Setup right panel.
            self.base,
            bg=theme['main']
        )
        self.right_panel_frame.place(  # Place right panel.
            x=scr_x - self.panel_size,
            y=0,
            width=self.panel_size,
            height=scr_y
        )
        self.right_panel_frame.grid_columnconfigure(0, weight=1)  # Center objects.
        self.plotfile = StringVar()  # Set variable for plot file.
        self.plotfile_label = self.full_label(self.right_panel_frame, self.plotfile)  # Get plot file label.
        self.plotfile_label.grid(row=0, columnspan=2)  # Place plotfile label.

        weights = [
            'weightxmin',
            'weightxmax',
            'weightymin',
            'weightymax'
        ]
        names = [
            'x min weight',
            'x max weight',
            'y min weight',
            'y max weight'
        ]
        r = 1
        for weight, name in zip(weights, names):
            self.full_label(self.right_panel_frame, name).grid(row=r, columnspan=2)
            r += 1
            exec(weight + "var = self.rt_data['" + weight + "']")
            self.full_button(
                self.right_panel_frame,
                'circle.png',
                lambda weight=weight: self.show_numpad(weight),  # Remember we need to declare x=x to instance the variable.
                eval(weight + 'var')
            ).grid(row=r, columnspan=2)
            r += 1

    def half_button(self, parent, image, command=None, text=None):
        """
        This creates a button that is half the panel width.
        """
        half_image = PhotoImage(file=img(image, 10, 10))
        half_button = Button(parent, image=half_image, command=command)
        half_button.image = half_image
        size = self.panel_size / 2
        half_button.configure(
            width=size,
            height=size,
        )
        half_button = config_button(half_button)
        if text:
            half_button = config_button_text(half_button, text)
        return half_button

    def full_button(self, parent, image, command=None, text=None):
        """
        This creates a button that is the full panel width.
        """
        sizex = self.panel_size,
        sizey = self.panel_size / 3
        frame = Frame(
            parent,
            width=sizex,
            height=sizey
        )
        full_image = PhotoImage(file=img(image, 20, 10))
        full_button = Button(frame, image=full_image, command=command)
        full_button.image = full_image
        full_button.configure(
            width=self.panel_size,
            height=self.panel_size / 3,
        )
        full_button = config_button(full_button)
        if text:
            full_button = config_button_text(full_button, text)
        full_button.pack()
        return frame

    def full_text_button(self, parent, command, text):
        """
        This presents us with a full width button containing text only.
        """
        sizex = self.panel_size
        sizey = int(self.panel_size / 3)
        print(sizex, sizey)
        frame = Frame(
            parent,
            width=sizex,
            height=sizey
        )
        full_button = Button(frame, textvariable=text, command=command)
        full_button.configure(
            width=sizex,
            height=sizey,
        )
        full_button = config_button_text(full_button, text)
        full_button.pack()
        return frame

    def full_label(self, parent, textvariable):
        """
        This will produce a subframe with a text label
        """
        frame = Frame(
            parent,
            width=self.panel_size,
            height=prx(5),
            bg=theme['main']
        )
        label = Label(
            frame
        )
        label = config_text(label, textvariable)
        label.pack(anchor='center')
        return frame

    def update_defaults(self):
        """
        This updates the default values we pass to the trajectory plotter.
        """
        for setting in self.rt_data:
            if setting in self.defaults.keys():
                u_set = self.rt_data[setting].get()
                if u_set.lstrip("-").isdigit():  # Confirm we have a number.
                    u_set = eval(u_set)  # Eval the setting back into a literal.
                self.defaults[setting] = u_set

    def get_plotfile(self):
        """
        This will open up a plot file and pass it to a variable.
        """
        self.rt_data['plotfile'] = openfile('/plots')
        self.plotfile.set(
            self.rt_data['plotfile'].split('/')[-1]
        )
        if self.plot:  # Clear if needed.
            self.plot.get_tk_widget().pack_forget()  # Clear old plot.

    def render_plotfile(self):
        """
        This will render the actual plots into the writer app.
        """
        self.update_defaults()  # update with latest config.
        plotfile = self.rt_data['plotfile']  # Fetch plot file.
        if plotfile:
            if self.plot:  # Clear if needed.
                self.plot.get_tk_widget().pack_forget()  # Clear old plot.
            self.plot = self.plotter(plotfile, self.plot_frame, theme, settings.defaults, 1, self.rt_data)  # TODO: This will need to be revised for simulations.
            self.plot.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH)  # Fetch canvas widget.
        return self.plot

    def show_numpad(self, varname):
        """
        Lifts the numberpad page.

        :param varname: String var to set.
        :type varname: str
        """
        # print(varname, self.rt_data[varname].get())
        self.temp['number'].set(varname)
        self.controller.show_frame("NumPad")


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
        global rt_data
        self.rt_data = rt_data
        self.rt_data['temp'] = dict()  # Create temp cache so we can push and pull variables around.
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
        for F in (Home, Writer, Audience, NumPad):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            if page_name == 'NumPad':
                frame.configure(
                    height=pry(50),
                    width=pry(50),
                    bg='grey',
                    borderwidth=pry(1),
                )
                frame.grid(row=0, column=0)
            else:
                frame.grid(row=0, column=0, sticky="nsew")

        # home.show()
        self.show_frame('Home')

    def show_frame(self, page_name):
        """
        Shows a frame...
        """
        frame = self.frames[page_name]
        frame.tkraise()


# noinspection PyShadowingNames
class NumPad(Frame):
    """
    Creates a simple number pad.
    """
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        global rt_data
        self.rt_data = rt_data
        self.temp = self.rt_data['temp']
        self.model = parent
        self.controller = controller
        self.grid()
        self.numvar = StringVar()
        self.numvar.set('')
        # print(self.numvar.get())
        self.number = None
        self.numpad_create()
        self.b = None
        self.dell = None
        self.go = None

    def get_num(self):
        """
        This fetches the target number StringVar value from the rt_data.
        :rtype: StringVar
        """
        return self.rt_data[self.temp['number'].get()]

    def set_num(self, number):
        """
        Sets or updates the number variable
        """
        number = str(number)
        if self.number:
            self.number += number
        else:
            self.number = number
        self.numvar.set(self.number)

    def pass_nums(self):
        """
        This passes our numbers to the parent model.
        """
        # print(self.numvar.get())
        if self.numvar.get():  # Prevent returning nulls.
            self.get_num().set(self.numvar.get())
            self.temp['number'].set('0')
        self.controller.show_frame('Writer')
        self.numvar.set('')
        self.number = None

    def delete_nums(self):
        """
        Removes the last number entered.
        """
        self.number = self.number[0:-1]
        self.numvar.set(self.number)

    def numpad_create(self):
        """
        Creates a simple number pad.
        """
        btn_list = [
            '7', '8', '9',
            '4', '5', '6',
            '1', '2', '3', '0'
        ]
        r = 1
        c = 0
        height = 3
        width = 4
        lb = Label(self, textvariable=self.numvar)
        config_number_button(lb)
        lb.grid(row=0, columnspan=3, sticky=(E, W))
        for b in btn_list:
            self.b = Button(self, text=b, width=width, height=height, command=lambda b=b: self.set_num(b))
            config_number_button(self.b)
            self.b.grid(row=r, column=c)
            c += 1
            if c > 2:
                c = 0
                r += 1
        self.dell = Button(self, text='del', width=width, height=height, command=lambda: self.delete_nums())
        config_number_button(self.dell)
        self.dell.grid(row=4, column=1)
        self.go = Button(self, text='go', width=width, height=height, command=lambda: self.pass_nums())
        config_number_button(self.go)
        self.go.grid(row=4, column=2)


def config_button(element):
    """
    This configures our button styles.
    """
    element.configure(
        activebackground=theme['main'],
        activeforeground=theme['buttontext'],
        foreground=theme['buttontext'],
        background=theme['main'],
        borderwidth=0,
        highlightthickness=0,
        relief=FLAT,
        compound='center'
    )
    return element


def config_number_button(element):
    """
    This styles the buttons on the number pad.
    """
    el = config_button(element)
    el.configure(
        font=('Helvetica', str(pointsy(5))),
    )


def config_text(element, text):
    """
    This takes an element and configures the text properties
    """
    element.configure(
        font=(theme['font'], pointsy(2)),
        pady=pry(2),
        fg=theme['text'],
        bg=theme['main'],
        compound='center'
    )
    if isinstance(text, tk.StringVar):
        element.configure(
            textvariable=text
        )
    else:
        element.configure(
            text=text
        )
    return element


def config_button_text(element, text):
    """
    This will configure our button text.
    """
    element = config_text(element, text)
    element.configure(
        fg=theme['buttontext']
    )
    return element


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


def prx(percent, use_float=False):
    """
    This ficures a percentage of x.
    """
    return percent_of(percent, scr_x, use_float)


def pry(percent, use_float=False):
    """
    This figures a percentage of y.
    """
    return percent_of(percent, scr_y, use_float)


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


def pointsy(percent):
    """
    This factors the point size of text in contrast to screen size.
    """
    pix_size = pry(percent)
    points = pix_size / 1.333
    return int(points)


def openfile(defdir):

    """
    Opens a file.
    """
    name = askopenfilename(
        initialdir=os.path.abspath(os.getcwd() + defdir),
        filetypes=[("Obj files", "*.obj")],
        title="Choose a file."
        )
    return name


# TODO: I have no idea if matplotlib is measuring the fontsize in points or pixels...
theme['fontsize'] = pointsy(theme['fontsize'])  # This is the fontsize for the matplotlib graphs.
theme['scattersize'] = pry(theme['scattersize'], True)
theme['pivotsize'] = pry(theme['pivotsize'])
theme['weightsize'] = pry(theme['weightsize'])
theme['linewidth'] = pry(theme['linewidth'], True)
app = MainView()
app.geometry(
    str(scr_x) + 'x' + str(scr_y) + '+0+0'
)
app.mainloop()
