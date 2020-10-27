"""
This is our top-level ux file

This is the main program loop for the user interface.

Tips for messed up X: https://www.ibm.com/support/pages/x11-forwarding-ssh-connection-rejected-because-wrong-authentication
NOTE: Copy the .Xauthority file from root to pi.

NOTE: THE X-SERVER MUST BE RUNNING!

Good REf: https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
Disable Screen blank: https://raspberrypi.stackexchange.com/questions/2059/disable-screen-blanking-in-x-windows-on-raspbian

TODO: NOTE!! Buttons and Labels are sized by the number of chars UNLESS they have an image!

TODO: We seriously need to break these inits down into classes...

TODO: Once we are satisfied with the operations we should really create a master class to clean up the inheritance.
"""
import os
import tkinter as tk
import uuid
import time
from warehouse.threading import Thread
from tkinter import *
from tkinter.filedialog import askopenfilename
import pyqrcode
from PIL import Image as PilImage, ImageTk as PilImageTk

# import settings
from settings import settings
from warehouse.system import system_command
from warehouse.math import percent_of, percent_in, center
from warehouse.utils import file_rename, str_quo as sq
from warehouse.uxutils import image_resize, miv
from writer.plot import pymesh_stl


scr_x, scr_y = settings.screensize

theme = settings.themes[settings.theme]
# defaults = settings.defaults

# This crap is for tunneling the app over ssh
os.environ['DISPLAY'] = settings.display
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])
system_command(['echo', '$DISPLAY'])
if 'localhost' not in settings.display:  # This will disable screen blackouts.
    system_command(['xset', 's', 'off', '-display', settings.display])
    system_command(['xset', '-dpms', '-display', settings.display])
    system_command(['xset', 's', 'noblank', '-display', settings.display])

rt_data = dict()


def get_spacer():
    """
    Returns a spacer image.
    """
    imgpth = os.getcwd() + '/img/base/spacer.png'
    return PhotoImage(file=imgpth)


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


class Widget(Frame):
    """
    This is a frame inheritor experiment to relax the complexity of the inits.
    """
    def __init__(self, controller):
        Frame.__init__(self)
        self.controller = controller


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

        self.writer_entry_button = self.entry_button('writer.png', command=lambda: controller.show_frame(
            "Writer"))  # Place entry buttons.
        self.audience_entry_button = self.entry_button('audience.png',
                                                       command=lambda: controller.show_frame("Audience"))
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
            ['sudo', 'service', 'pc', 'restart']
        )


class Writer(Frame):
    """
    Writer Page.
    """

    # noinspection PyShadowingNames
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.rt_data = self.controller.rt_data
        self.defaults = self.controller.defaults
        self.rt_data['plotfile'] = str()
        self.folder = None
        self.ext = None
        self.rt_data['0'] = StringVar()
        self.rt_data['0'].set('0')

        self.temp = self.rt_data['temp']  # Create temp cache so we can push and pull variables around.
        self.temp['number'] = StringVar()
        self.temp['number'].set('0')
        self.temp['word'] = StringVar()
        self.temp['word'].set('')
        self.temp['file'] = StringVar()
        self.temp['file'].set('')
        self.temp['ext'] = '.obj'
        self.temp['folder'] = settings.plot_dir
        self.temp['targetfile'] = StringVar()
        self.temp['qr_data'] = str({
            'ssid': settings.ssid,
            'secret': settings.secret,
            'enc': 'WPA',
            'directorid': settings.director_id,
            'stageid': str(uuid.uuid4()),
            'rsa_pub': 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCQV2BjlfjrMtVieIJ5IrJyar9zjaL8XvWKyDgoc5rwvvkWimd+m4rbhgeyAAvCQLzL8xINhP88zqWA3sswvEgUGrZzqocM0AaCrVc2AwDsWFLEAtxFu+7rsKWcFlg9jZX2NvmE+FFnqoCIcPQK+vEDa6dv40xmFWankAXTvq2gYQIDAQAB'
        })
        self.numpad = NumPad(self, self.controller)
        self.plotter = pymesh_stl
        self.number = None  # Temp space for passing numbers.
        self.word = None  # Temp space for passing words.
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
            height=scr_y,
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
        # TODO: Stuff this into a loop.
        render = StringVar()
        self.render_button = self.full_button(  # TODO: We need to add a save dialog here.
            self.left_panel_frame,
            'fullbuttonframe.png',
            command=self.render_plotfile,
            text='audition'
        )
        self.render_button.grid(row=1, columnspan=2)
        render.set('Render')
        self.rehersal_button = self.full_button(
            self.left_panel_frame,
            'fullbuttonframe.png',
            command=lambda: self.show_rehearsal(),
            text='rehearsal'
        )
        self.rehersal_button.grid(row=2, columnspan=2)
        self.publish_button = self.full_button(
            self.left_panel_frame,
            'fullbuttonframe.png',
            command='',
            text='publish'
        )
        self.publish_button.grid(row=3, columnspan=2)
        self.calibrate_button = self.full_button(
            self.left_panel_frame,
            'fullbuttonframe.png',
            command=lambda: self.show_calibrations(),
            text='calibrate'
        )
        self.calibrate_button.grid(row=4, columnspan=2)
        self.share_button = self.full_button(
            self.left_panel_frame,
            'fullbuttonframe.png',
            command='',
            text='share'
        )
        self.share_button.grid(row=5, columnspan=2)
        self.receive_button = self.full_button(
            self.left_panel_frame,
            'fullbuttonframe.png',
            command=lambda: self.show_keyboard('key_test'),
            text='receive'
        )
        self.receive_button.grid(row=6, columnspan=2)
        self.pair_button = self.full_button(
            self.left_panel_frame,
            'fullbuttonframe.png',
            command=lambda: self.show_qr_code(),
            text='pairing'
        )
        self.pair_button.grid(row=7, columnspan=2)

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
            'weightymax',
            'contact'
        ]
        names = [
            'x min weight',
            'x max weight',
            'y min weight',
            'y max weight',
            'contact'
        ]
        r = 1
        for weight, name in zip(weights, names):
            self.full_label(self.right_panel_frame, name).grid(row=r, columnspan=2)
            r += 1
            exec(weight + "var = self.rt_data['" + weight + "']")
            self.full_button(
                self.right_panel_frame,
                'circle.png',
                lambda weight=weight: self.show_numpad(weight),
                # Remember we need to declare x=x to instance the variable.
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
            height=self.panel_size / 5 - 5,
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
        for setting in self.controller.rt_data:
            if setting in self.controller.defaults.keys():
                u_set = self.controller.rt_data[setting].get()
                if u_set.lstrip("-").isdigit():  # Confirm we have a number.
                    u_set = eval(u_set)  # Eval the setting back into a literal.
                elif not u_set[-1].isalnum():  # Handle dicts and arrays.
                    u_set = eval(u_set)
                    # print('evaluating exception')
                    # print(type(self.controller.defaults[setting]), self.controller.defaults[setting])
                self.controller.defaults[setting] = u_set
        self.defaults = self.controller.defaults

    def get_plotfile(self):
        """
        This will open up a plot file and pass it to a variable.
        """
        self.ext = self.temp['ext'] = '.obj'
        self.folder = self.temp['folder'] = settings.plot_dir  # Get working directory.
        self.show_file_browser('folder')
        # self.rt_data['plotfile'] = openfile('/plots')

    def render_plotfile(self):
        """
        This will render the actual plots into the writer app.
        """
        plotfile = self.rt_data['plotfile'] = self.temp['targetfile'].get()  # Fetch plot file.
        if plotfile:
            self.controller.show_frame('LoadingIcon')  # Raise loading icon.

        if self.plot:  # Clear if needed.
            self.plot.get_tk_widget().pack_forget()  # Clear old plot.
        self.update_defaults()  # update with latest config.

        self.plotfile.set(  # Update filename label.
            self.rt_data['plotfile'].split('/')[-1]
        )
        if plotfile:
            if self.plot:  # Clear if needed.
                self.plot.get_tk_widget().pack_forget()  # Clear old plot.
            self.plot = self.plotter(
                self.controller,
                self.plot_frame,
                theme,
                plotfile,
                1,
            )  # TODO: This will need to be revised for simulations.
            self.plot.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH)  # Fetch canvas widget.
        self.controller.show_frame('Writer')  # Hide loading icon.
        if self.plot:
            self.controller.has_plot = True
        return self.plot

    def show_numpad(self, varname):
        """
        Lifts the numberpad page.

        TODO: We need to figure out some sore of clamp so we can prevent impossible numbers from being entered.

        :param varname: String var to set.
        :type varname: str
        """
        # print(varname, self.rt_data[varname].get())
        self.controller.target = 'Writer'
        self.temp['number'].set(varname)
        safe_raise(self.controller, 'NumPad', 'Writer')
        self.controller.show_frame('CloseWidget')

    def show_keyboard(self, varname):
        """
        Lifts the keyboard page.
        """
        self.controller.target = 'Writer'
        self.temp['word'].set(varname)
        safe_raise(self.controller, 'Keyboard', 'Writer')
        self.controller.show_frame('CloseWidget')

    def show_file_browser(self, varname):
        """
        Lifts the file browser page.
        """
        self.temp[varname] = os.getcwd() + '/' + settings.plot_dir
        self.controller.clear('FileBrowser')
        safe_raise(self.controller, 'FileBrowser', 'Writer')
        self.controller.show_frame('CloseWidget')

    def show_qr_code(self):
        """
        This will create and show a QR code reflecting the temp data stored in key qr_data.
        """

        safe_raise(self.controller, 'QRCodeWidget', 'Writer')
        self.controller.refresh('QRCodeWidget')
        self.controller.show_frame('CloseWidget')
        qr_data = eval(self.temp['qr_data'])
        # TODO: We may need to investigate additional handling of this during the pairing procedure.
        qr_data['stageid'] = str(uuid.uuid4())  # Refresh id for the next stage.
        self.temp['qr_data'] = str(qr_data)
        print(self.temp['qr_data'])

    def show_rehearsal(self):
        """
        This will raise the rehersal frame.
        """
        self.controller.refresh('Rehearsal')
        safe_raise(self.controller, 'Rehearsal', 'Writer')
        self.controller.show_frame('CloseWidget')

    def show_calibrations(self):
        """
        This will raise the calibrations frame.
        """
        self.controller.refresh('Calibrations')  # This clamps duplicate stage entries.
        safe_raise(self.controller, 'Calibrations', 'Writer')
        self.controller.show_frame('CloseWidget')


class Rehearsal(Frame):
    """
    This is the audition interface.

    weightxmin',
    weightxmax',
    weightymin',
    weightymax',
    contact'
    """

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.rt_data = controller.rt_data
        self.temp = self.rt_data['temp']
        self.settings = self.controller.settings
        self.rehearsaldata = self.temp['rehearsaldata'] = None
        self.rehearsalname = self.temp['rehearsalname'] = StringVar()
        self.rehearsal_buttons = list()
        self.rehearsal_rename = str()
        self.stagedata = self.temp['stagedata']
        self.stagetarget = self.temp['stagetarget']
        self.stagename = StringVar()
        self.stagename.set('')
        self.details = StringVar()
        self.script_class = self.temp['script_class'] = StringVar()
        self.script_type = self.temp['script_type'] = StringVar()
        self.script_scaler = self.temp['script_scaler'] = StringVar()
        self.script = dict()
        self.stage_id = str()
        self.stage_buttons = list()
        self.spacer = get_spacer()
        #  ##############
        #  class selector
        #  ##############
        self.classes = Frame(
            self,
            bg=theme['main'],
            highlightthickness=pry(1),
            highlightbackground=theme['entrybackground']
        )
        self.classes.place(  # These use static values as we don't resize animations (yet).
            width=prx(39),
            height=pry(75),
            x=cp(prx(35), 494),
            y=cp(pry(45), pry(75))
        )
        self.classes.grid_columnconfigure(0, weight=1)
        self.classes.grid_rowconfigure(1, weight=1)
        self.class_label = GifIcon(
            self.classes,
            'animal-gaits.gif',
            (35, 35)
        )
        self.class_label.configure(
            bg='white',
        )
        self.class_label.grid(row=0, column=0)
        self.class_selection_frame = Frame(
            self.classes,
            bg=theme['main']
        )
        self.class_selection_frame.grid(row=1, column=0)

        button_array(
            self.class_selection_frame,
            ['walk', 'amble', 'pace'],
            [
                lambda: self.select_class('walk'),
                lambda: self.select_class('amble'),
                lambda: self.select_class('pace')
            ],
        )
        button_array(
            self.class_selection_frame,
            ['trot', 'canter', 'gallup'],
            [
                lambda: self.select_class('trot'),
                lambda: self.select_class('canter'),
                lambda: self.select_class('gallup')
            ],
            rw=1,
        )
        #  ###############
        #  scaler selector
        #  ###############
        self.scalers = Frame(
            self,
            bg=theme['main'],
            highlightthickness=pry(1),
            highlightbackground=theme['entrybackground']
        )
        self.scalers.place(
            width=prx(30),
            height=pry(45),
            x=cp(prx(35), 360),
            y=cp(pry(45), pry(45))
        )
        self.scalers.grid_rowconfigure(0, weight=1)
        self.scalers.grid_columnconfigure(0, weight=1)
        self.scaler_icon_frame = Frame(
            self.scalers,
            bg=theme['main'],
            width=355
        )
        self.scaler_icon_frame.grid(row=0, column=0)
        self.scaler_icon_frame.grid_columnconfigure(0, weight=1)
        self.rotate_label = GifIcon(
            self.scaler_icon_frame,
            'rotate.gif',
            (25, 25)
        )
        self.rotate_label.grid(row=0, column=0)
        self.sidestep_label = GifIcon(
            self.scaler_icon_frame,
            'sidestep.gif',
            (25, 25)
        )
        self.sidestep_label.grid(row=0, column=1)
        button_array(
            self.scaler_icon_frame,
            ['rotate', 'sidestep'],
            [
                lambda: self.select_scaler('rotate'),
                lambda: self.select_scaler('sidestep')
            ],
            rw=1,
        )
        self.scaler_cancel_frame = Frame(
            self.scaler_icon_frame,
            width=355
        )
        self.scaler_cancel_frame.grid(row=2, columnspan=2)
        button_array(
            self.scaler_cancel_frame,
            ['cancel'],
            [lambda: self.select_scaler('none')],
            rw=2,
        )
        #  ##############
        #  open rehearsal
        #  ##############
        self.open_frame = Frame(
            self,
            bg=theme['main'],
            highlightthickness=pry(1),
            highlightbackground=theme['entrybackground']
        )
        self.open_frame.place(
            width=prx(50),
            height=pry(80),
            x=cp(prx(35), prx(50)),
            y=cp(pry(45), pry(80))
        )
        self.rehearsal_selector_frame = Frame(
            self.open_frame,
            width=prx(48),
            height=pry(60),
            bg=theme['main']
        )
        self.rehearsal_selector_frame.grid(row=0, column=0)
        self.rehearsal_selector_frame.grid_columnconfigure(0, weight=1)
        self.rehearsal_selector = VerticalScrolledFrame(self.rehearsal_selector_frame, prx(48), pry(65))
        self.rehearsal_selector.pack()
        self.cancel_rehearsal_open = Frame(
            self.open_frame,
            width=prx(50),
            height=pry(10),
            bg=theme['main']
        )
        self.cancel_rehearsal_open.grid(row=1, column=0)
        button_array(
            self.cancel_rehearsal_open,
            ['cancel'],
            [lambda: self.cancel_rehearsal()],
        )
        #  ##################
        #  configure compound
        #  ##################
        self.compound = self.temp['compound'] = dict()  # Init compound data.
        """
        Note that these values will be string and int variables.
        {
            '1': {
                'rehearsal': 'test_leg_1_path',
                'timing': 1,
                'reverse': True,
                'mirror': False
            },
            '2': {}.....
        }
        """
        for idx in range(1, 5):  # Define compound data variables.
            idx = str(idx)
            cpi = self.compound[idx] = dict()
            cpi['rehearsal'] = StringVar()
            cpi['timing'] = IntVar()
            cpi['reverse'] = IntVar()
            cpi['mirror'] = IntVar()

        self.compound_frame = Frame(
            self,
            bg=theme['main'],
            highlightthickness=pry(1),
            highlightbackground=theme['entrybackground']
        )
        self.compound_frame.place(
            width=prx(51),
            height=pry(94),
            x=cp(prx(35), prx(51)),
            y=cp(pry(47), pry(94))
        )
        self.compound_frame.grid_columnconfigure(0, weight=1)
        self.compound_frame.grid_columnconfigure(1, weight=1)
        self.compound_frame.grid_columnconfigure(2, weight=1)
        self.compound_left = Frame(
            self.compound_frame,
            bg=theme['main']
        )
        # TODO: Stuff the compound widgets into a loop.
        self.compound_left.grid(row=0, column=0)
        self.comp4_rev = IntVar()
        self.comp4_mir = IntVar()
        self.comp4_txt = StringVar()
        self.comp4_txt.set('open')
        self.compound_4 = self.compound_open(
            self.compound_left,
            'leg 4',
            self.comp4_txt,
            self.comp4_rev,
            self.comp4_mir,
            lambda: self.list_rehearsals(self.compound_frame, 4)
        )
        self.compound_4.grid(row=0, column=0)
        self.comp2_rev = IntVar()
        self.comp2_mir = IntVar()
        self.comp2_txt = StringVar()
        self.comp2_txt.set('open')
        self.compound_2 = self.compound_open(
            self.compound_left,
            'leg 2',
            self.comp2_txt,
            self.comp2_rev,
            self.comp2_mir,
            lambda: self.list_rehearsals(self.compound_frame, 2)
        )
        self.compound_2.grid(row=1, column=0)
        self.compound_graphic_frame = Frame(
            self.compound_frame,
            height=pry(70),
        )
        self.compound_graphic_frame.grid(row=0, rowspan=2, column=1, sticky=(N, S, E, W))
        self.compound_graphic = PhotoImage(file=img('quad_front.png', 20, 70))
        self.compound_graphic_label = Label(
            self.compound_graphic_frame,
            image=self.compound_graphic,
            bg=theme['main'],
            width=prx(22),
            height=pry(59)
        )
        self.compound_graphic_label.image = self.compound_graphic
        self.compound_graphic_label.pack(fill="both", expand=True)
        self.compound_right = Frame(
            self.compound_frame,
            bg=theme['main']
        )
        self.compound_right.grid(row=0, column=2)
        self.comp3_rev = IntVar()
        self.comp3_mir = IntVar()
        self.comp3_txt = StringVar()
        self.comp3_txt.set('open')
        self.compound_3 = self.compound_open(
            self.compound_right,
            'leg 3',
            self.comp3_txt,
            self.comp3_rev,
            self.comp3_mir,
            lambda: self.list_rehearsals(self.compound_frame, 3)
        )
        self.compound_3.grid(row=0, column=0)
        self.comp1_rev = IntVar()
        self.comp1_mir = IntVar()
        self.comp1_txt = StringVar()
        self.comp1_txt.set('open')
        self.compound_1 = self.compound_open(
            self.compound_right,
            'leg 1',
            self.comp1_txt,
            self.comp1_rev,
            self.comp1_mir,
            lambda: self.list_rehearsals(self.compound_frame, 1)
        )
        self.compound_1.grid(row=1, column=0)
        self.timing1 = self.timing2 = self.timing3 = self.timing4 = Scale()

        self.t1 = IntVar()
        self.t2 = IntVar()
        self.t3 = IntVar()
        self.t4 = IntVar()
        self.timing_frame = self.timing_slider(
            self.compound_frame,
            self.t1,
            self.t2,
            self.t3,
            self.t4,
            # ['1', '2', '3', '4']
        )
        self.timing_frame.grid(row=2, columnspan=3)
        #  ##############
        #  configure base
        #  ##############
        self.base = Frame(
            self,
            bg=theme['main'],
            width=prx(70),
            height=pry(94)
        )
        self.base.place(  # Place Base.
            width=prx(70),
            height=pry(94)
        )
        #  ##########
        #  Left panel
        #  ##########
        self.stage_title_frame = Frame(  # Place title.
            self.base,
            width=prx(20),
            height=pry(10),
        )
        self.stage_title_frame.grid(row=0, column=0)
        Label(
            self.stage_title_frame,
            text='stage selection:',
            bg=theme['main'],
            fg=theme['buttontext'],
            pady=pry(2)
        ).pack()
        self.stage_selector = Frame(  # Place scroll list.
            self.base,
            width=prx(20),
            height=pry(70),
            bg='red'
        )
        self.stage_selector.grid(row=1, column=0, sticky=N)
        self.stage_list = VerticalScrolledFrame(self.stage_selector, width=prx(20))
        self.stage_list.pack()
        self.selected_stage_frame = Frame(
            self.base,
            width=prx(20),
            height=pry(10),
            bg=theme['main'],
        )
        self.selected_stage_frame.grid(row=2, column=0, sticky="nsew")  # Place selected stage.
        Label(
            self.selected_stage_frame,
            textvariable=self.stagename,
            bg=theme['main'],
            fg=theme['buttontext'],
            pady=pry(2)
        ).pack(side=TOP, expand=YES)

        self.list_stages()

        #  ###########
        #  Right panel
        #  ###########
        self.right_panel_frame = Frame(  # Frame section.
            self.base,
            height=pry(90),
            width=prx(20),
            bg=theme['main'],
        )
        self.right_panel_frame.grid(row=0, rowspan=3, column=1, sticky=N)  # Frame right panel.
        button_array(  # Make top buttons.
            self.right_panel_frame,
            ['save', 'open', 'rename', 'delete'],
            [
                lambda: self.save_rehearsal(),
                lambda: self.list_rehearsals(),
                lambda: self.save_rehearsal(rename=str(self.rehearsalname.get())),
                lambda: self.delete_rehearsal()
            ],
        )
        self.details_frame = Frame(  # Frame details.
            self.right_panel_frame,
            width=prx(40),
            height=pry(67),
            bg=theme['main'],
        )
        self.details_frame.grid(row=1, columnspan=4)
        Label(
            self.details_frame,
            textvariable=self.details,
            image=get_spacer(),
            height=pry(67),
            width=prx(33),
            compound='center',
            bg=theme['main'],
            fg=theme['buttontext'],
            padx=prx(2),
            anchor=W,
            justify=LEFT
        ).grid(row=0, column=0, sticky=E)
        self.right_panel_buttons_frame = Frame(
            self.details_frame,
            height=pry(67),
            width=prx(15)
        )
        self.right_panel_buttons_frame.grid(row=0, column=1, sticky=E)
        button_array(
            self.right_panel_buttons_frame,
            ['import', 'class', 'run', 'compound', 'scaler'],
            [
                lambda: self.import_rehearsals(),
                lambda: self.class_selector(),
                lambda: self.run_rehearsal(),
                lambda: self.compound_selector(),
                lambda: self.scaler_selector()
            ],
            col=1,
            vert=True
        )

        self.velocity = StringVar()
        self.velocity.set('velocity: ' + str(settings.defaults['velocity']))
        self.offset = StringVar()
        self.offset.set('offset: ' + str(settings.defaults['offset']))
        button_array(  # Make bottom buttons.
            self.right_panel_frame,
            ['dry', 'live', self.offset, self.velocity],
            [
                lambda: self.textvar_button_event('dry', self.script_type),
                lambda: self.textvar_button_event('live', self.script_type),
                lambda: self.show_numpad('offset'),
                lambda: self.show_numpad('velocity')
            ],
            rw=2,
        )

    def show_numpad(self, varname):
        """
        Presents the num pad.
        """
        self.controller.target = self.temp['targetframe'] = 'Rehearsal'
        self.controller.command = self.refresh
        self.temp['number'].set(varname)
        safe_raise(self.controller, 'NumPad', 'Rehearsal')
        self.controller.show_frame('CloseWidget')

    def assemble_details(self):
        """
        This assembles the audition details and updates the details string var.
        """
        if self.controller.has_plot or self.rehearsalname:
            text = 'Statitistics:\n'
            if self.rehearsalname.get():
                text += '\nrehearsal: ' + self.rehearsalname.get() + ',\n'
            if self.stagename.get():
                text += '\n' + self.stagename.get() + ',\n'
            else:
                text += '\nPlease select a stage**\n'
            text += '\nweight x min: ' + self.rt_data[
                'weightxmin'
            ].get() + ', \tweight x max: ' + self.rt_data[
                        'weightxmax'
                    ].get() + ',\n'
            text += '\nweight y min: ' + self.rt_data[
                'weightymin'
            ].get() + ', \tweight y max: ' + self.rt_data[
                        'weightymax'
                    ].get() + ',\n'
            text += '\n' + self.velocity.get() + ', \t' + self.offset.get() + ',\n'
            if self.script_class.get():
                text += '\nclassification: ' + self.script_class.get() + ',\n'
            else:
                text += '\nPlease specify classification**\n'
            if not self.script_scaler.get():
                self.script_scaler.set('none')
            text += '\nscaler: ' + self.script_scaler.get() + ',\n'
            if self.script_type.get():
                text += '\ntype: ' + self.script_type.get() + ',\n'
            else:
                text += '\nPlease specify type**'
        else:
            text = 'Please create audition, or load rehearsal**'

        self.details.set(text)

    def textvar_button_event(self, text, var):
        """
        This just sets a text variable and refreshed the data.
        """
        var.set(text)
        self.refresh()

    def list_stages(self):
        """
        This produces the list of stages that we have been paired with.
        """
        list_stages(self, self.stage_list)

    def select_stage(self, s_id, s_name):
        """
        This is the stage selection event.
        """
        select_stage(self, s_id, s_name)

    def class_selector(self):
        """
        Raises the class selector frame and starts the animation.
        """
        self.class_label.gif.go = True
        safe_raise(False, self.classes, self.base)

    def select_class(self, c_name='custom'):
        """
        This sets the script class variable and raises self.
        Stops the animation.
        """
        self.script_class.set(c_name)
        if c_name != 'custom':
            print(type(self.controller.defaults['timings']), self.controller.defaults['timings'])
            tmg = self.controller.defaults['timings'][c_name]
            self.refresh()
            self.base.tkraise()
            self.class_label.gif.go = False
            for tm in range(4):
                exec("self.timing" + str(tm + 1) + '.set(' + str(tmg[tm]) + ')')
                # print("self.timing" + str(tm + 1) + '.set(' + str(tmg[tm]) + ')')
            for idx, md in enumerate(range(3, 7)):
                dm = idx + 1
                tg = tmg[md + 1]
                exe = [
                    "self.comp" + str(dm) + '_rev.set(' + str(tg[0]) + ')',
                    "self.comp" + str(dm) + '_mir.set(' + str(tg[1]) + ')'
                ]
                for ex in exe:
                    exec(ex)
        else:
            # TODO: We are going to move this to the custom submit event.
            # print(c_name)
            # print('populate custom class timings and jazz here')
            pass

    def scaler_selector(self):
        """
        Lifts the scaler selection frame.
        """
        self.rotate_label.gif.go = True
        self.sidestep_label.gif.go = True
        safe_raise(False, self.scalers, self.base)

    def select_scaler(self, s_name):
        """
        Selects the script scaler and lifts base.
        """

        def update_mir_rev(inh, mirs, revs):
            """
            This updates the mirror and reverse variables depending on what kind of scaler we are using.
            """
            mirvars = [
                inh.comp1_mir,
                inh.comp2_mir,
                inh.comp3_mir,
                inh.comp4_mir
            ]
            revvars = [
                inh.comp1_rev,
                inh.comp2_rev,
                inh.comp3_rev,
                inh.comp4_rev
            ]
            for idx, (mir, rev) in enumerate(zip(mirs, revs)):
                mirvars[idx].set(mir)
                revvars[idx].set(rev)

        self.script_scaler.set(s_name)
        self.refresh()
        self.base.tkraise()
        self.rotate_label.gif.go = False
        self.sidestep_label.gif.go = False
        if s_name == 'rotate':
            update_mir_rev(self, [0, 1, 0, 0], [0, 0, 1, 1])
        elif s_name == 'sidestep':
            update_mir_rev(self, [0, 0, 0, 0], [0, 0, 0, 0])

    def list_rehearsals(self, target=None, add=0):
        """
        Creates a list of saved rehearsals.
        """
        for rh in settings.rehearsals:
            rname = rh,
            rdata = settings.rehearsals[rh]
            self.rehearsal_buttons.append(
                config_rehearsallist_button(
                    Button(
                        self.rehearsal_selector.interior,
                        text=rname,
                        command=lambda q=(rh, rdata, target, add): self.open_rehearsal(*q),
                    )
                )
            )
            self.rehearsal_buttons[-1].pack()
            safe_raise(False, self.open_frame, self.base)

    def open_rehearsal(self, rname, rdata, target=None, add=0):
        """
        This will open one of our saved rehearsals.
        """
        if add:
            exec('self.comp' + str(add) + "_txt.set('" + rname + "')")
            # TODO: Here is where we will need to add individual compound plots to the rehearsal data
        self.rehearsalname.set(rname)  # TODO: we need to figure out how we are going to lay out the rehearsal data model.
        self.rehearsaldata = rdata
        self.cancel_rehearsal()
        self.controller.target = ['Writer', 'Rehearsal', 'CloseWidget']
        if target:
            target.tkraise()

    def cancel_rehearsal(self):
        """
        This cancels out of the open rehearsal dialog.
        """
        self.base.tkraise()
        self.refresh()
        self.controller.target = 'Writer'

    def import_rehearsals(self):
        """
        This is where we will import external rehearsals.
        """
        print('Importing rehearsal!')
        self.cancel_rehearsal()

    def run_rehearsal(self):
        """
        This is where we will send the rehearsal to the downstream stage and acquire the results.
        """
        print('running rehearsal')
        self.cancel_rehearsal()
        self.controller.show_frame('Writer')
        self.controller.target = 'Writer'

    def save_rehearsal(self, rename=''):
        """
        This will allow us to save the existing rehearsal.

        TODO: We need to add an overwrite confirmation and a cancel feature.
        """
        self.rehearsal_rename = rename
        self.controller.target = ['Writer', 'Rehearsal', 'CloseWidget']
        if not self.rehearsaldata:
            self.temp['error_message'].set('error: no rehearsal data available to save.')
            self.controller.show_frame('ErrorWidget')
        else:
            self.rt_data['rehearsalname'] = self.rehearsalname
            self.temp['word'].set('rehearsalname')
            if self.rehearsalname.get():
                self.temp['default_keyboard_text'] = self.rehearsalname
            self.controller.command = self.save_rehearsal_event
            self.controller.refresh('Keyboard')
            self.controller.show_frame('Keyboard')

    def save_rehearsal_event(self):
        """
        This commits the rehearsal data to disk and drops the keyboard
        """
        self.rehearsalname = self.rt_data['rehearsalname']
        if self.rehearsal_rename:
            del settings.rehearsals[self.rehearsal_rename]
            self.rehearsal_rename = ''
        settings.rehearsals[self.rehearsalname.get()] = self.rehearsaldata  # Revise temp settings model.
        settings.set('rehearsals')  # Revise permanent model.
        settings.save()  # Save permanent settings model to disk.
        self.refresh()  # Refresh data.
        safe_drop(self.controller, ['Writer', 'Rehearsal', 'CloseWidget'])
        self.controller.target = 'Writer'

    def delete_rehearsal(self):
        """
        Removes a rehearsal.
        """
        self.controller.target = 'Rehearsal'
        if not self.rehearsaldata:
            self.temp['error_message'].set('error: no rehearsal data available to delete.')
            self.controller.show_frame('ErrorWidget')
        else:
            self.temp['confirmation_message'].set('delete:' + self.rehearsalname.get() + '?')
            self.controller.command = self.delete_event
            self.controller.show_frame('ConfirmationWidget')

    def delete_event(self):
        """
        Actual delete action.
        """
        print('deleting')
        del settings.rehearsals[self.rehearsalname.get()]
        settings.set('rehearsals')  # Revise permanent model.
        settings.save()  # Save permanent settings model to disk.
        self.refresh()  # Refresh data.

    def compound_selector(self):
        """
        This shows the compound editor frame
        """
        # self.controller.target = 'Rehearsal'
        self.compound_frame.tkraise()

    def compound_open(self, parent, title, tvar, revvar, mirvar, command):
        """
        This is the widget we will use for selecting a compound rehersal.
        """
        container = Frame(  # Build base.
            parent,
            width=prx(21.6),
            height=pry(40),
            bg=theme['main']
        )
        container.grid_columnconfigure(0, weight=1)
        ti_frame = Frame(  # Build title frame.
            container,
            width=prx(21.6),
            height=pry(10),
        )
        ti_frame.grid(row=0, column=0)  # Create title label.
        til = config_text(
            Label(
                ti_frame
            ),
            title,
            4
        )
        til.pack()
        btn_frame = Frame(  # Create frame to hold buttons.
            container,
            width=prx(21.6),
            height=pry(10)
        )
        btn_frame.grid(row=1, column=0)
        config_single_button(  # Create open button.
            btn_frame,
            tvar,
            command
        )
        chk_frame = Frame(  # Create frame to hold checkboxs.
            container,
            width=prx(10),
            height=pry(10),
            bg=theme['main'],
        )
        chk_frame.grid(row=2, column=0)  # Create reverse checkbox.
        config_checkbox(
            chk_frame,
            '',
            revvar
        )
        Label(  # Create spacer.
            chk_frame,
            width=prx(3),
            image=get_spacer(),
            bg=theme['main']
        ).pack(side=LEFT)
        config_checkbox(  # Create mirror checkbox.
            chk_frame,
            '',
            mirvar
        )
        lbl_frame = Frame(  # Create label frame.
            container,
            width=prx(21.6),
            height=pry(10)
        )
        lbl_frame.grid(row=3, column=0)
        rev_btn = config_button(  # Create reverse button.
            Button(
                lbl_frame,
                text='reverse',
                height=pry(3),
                width=prx(5),
                image=self.spacer,
                command=lambda: chkvar_handler(revvar)
            )
        )
        rev_btn.image = self.spacer
        rev_btn.pack(side=LEFT)
        mir_btn = config_button(  # Create mirror button.
            Button(
                lbl_frame,
                text='mirror',
                height=pry(3),
                width=prx(5),
                image=self.spacer,
                command=lambda: chkvar_handler(mirvar)
            )
        )
        mir_btn.image = self.spacer
        mir_btn.pack(side=LEFT)
        return container

    def compound_cancel_event(self):
        """
        This cancels out of the compound dialog.
        """
        self.controller.target = 'Writer'
        self.base.tkraise()

    def compound_submit_event(self):
        """
        This submits the changes made in the compound window.
        """
        self.controller.target = 'Writer'
        self.refresh()
        self.base.tkraise()

    # noinspection PyMethodMayBeStatic
    def timing_slider(self, parent, t1, t2, t3, t4, names=None):
        """
        Creates four slider widgets for timing adjustment.

        TODO: This needs to be cleaned up.
        """
        if not names:
            names = ['', '', '', '']
        slider_frame = Frame(
            parent,
            width=prx(51),
            height=pry(35),
            bg=theme['main']
        )
        btn_frame = Frame(
            slider_frame,
            width=prx(51),
            bg=theme['main'],
        )
        btn_frame.pack(side=TOP)
        bmg = PhotoImage(file=img('fullbuttonframe.png', 8, 3, aspect=False))
        s_button = Button(
            btn_frame,
            width=prx(8),
            height=pry(3),
            text='submit',
            image=bmg,
            compound=CENTER,
            activebackground=theme['main'],
            activeforeground=theme['buttontext'],
            foreground=theme['buttontext'],
            background=theme['main'],
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.compound_submit_event(),
        )
        s_button.image = bmg
        s_button.pack(side=LEFT)
        Label(
            btn_frame,
            width=prx(16),
            height=pry(2),
            pady=pry(1),
            image=get_spacer(),
            compound='center',
            text='timing adjustment',
            bg=theme['main'],
            fg=theme['buttontext'],
        ).pack(side=LEFT)
        c_button = Button(
            btn_frame,
            width=prx(8),
            height=pry(1),
            text='cancel',
            image=bmg,
            compound='center',
            activebackground=theme['main'],
            activeforeground=theme['buttontext'],
            foreground=theme['buttontext'],
            background=theme['main'],
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.compound_cancel_event(),
        )
        c_button.pack(side=LEFT)
        for idx, (name, slider) in enumerate(zip(  # Loop to create sliders.
                names,
                [
                    t1,
                    t2,
                    t3,
                    t4
                ])):
            slide_frame = Frame(
                slider_frame,
                width=pry(49),
                height=pry(3),
                bg=theme['main']
            )
            slide_frame.pack(side=TOP)
            sc_label = config_text(
                element=Label(
                    slide_frame,
                    width=prx(3),
                    height=pry(2),
                    image=self.controller.spacer,
                    justify=LEFT,
                ),
                text=str(idx + 1),
                # size=2
            )
            sc_label.pack(side=LEFT)
            sc = Scale(
                slide_frame,
                width=pry(3),
                length=prx(45),
                variable=slider,
                label=name,
                orient=HORIZONTAL,
                bg=theme['main'],
                fg=theme['buttontext'],
                bd=0,
                troughcolor=theme['slidecolor'],
                highlightthickness=0,
                bigincrement=5,
                command=lambda q: self.select_class()
            )
            sc.pack()
            exec('self.timing' + str(idx + 1) + ' = sc')
        return slider_frame

    def update_compound(self):
        """
        This refreshes the compound data model.
        """
        reh = StringVar()
        for idx in range(4):
            idx = str(idx + 1)
            dt = self.compound[idx]

            exe = [  # Update leg properties.
                "dt['timing'] = self.timing" + idx,
                "dt['reverse'] = self.comp" + idx + '_rev',
                "dt['mirror'] = self.comp" + idx + '_mir'
            ]
            for ex in exe:
                # print(ex)
                exec(ex)
            exec('reh = self.comp' + idx + '_txt')
            if reh.get() != 'open':  # Set string vars for button text.
                dt['rehearsal'] = reh.get()
        # print(self.compound)

    def show_confirmation(self, message, command):
        """
        This shows the confirmation widget and passes a command event.
        """
        self.controller.target = 'Rehearsal'
        self.controller.command = command
        self.temp['confirmation_message'].set(message)
        safe_raise(self.controller, 'ConfirmationWidget', 'Rehearsal')

    def error_event(self, message):
        """
        This creates an error dialog showing the self.error string var.
        """
        self.controller.target = 'Rehearsal'
        self.temp['error_message'].set(message)
        self.temp['last_target'] = 'Writer'
        safe_raise(self.controller, 'ErrorWidget', 'Rehearsal')

    def refresh(self):
        """
        This allows the controller to trigger a refresh of the stage listings.
        """
        for buttons in [
            self.stage_buttons,
            self.rehearsal_buttons
        ]:
            for button in buttons:
                button.destroy()

        self.velocity.set('velocity: ' + str(self.rt_data['velocity'].get()))
        self.offset.set('offset: ' + str(self.rt_data['offset'].get()))
        self.assemble_details()
        self.update_compound()
        self.list_stages()
        self.controller.target = 'Writer'

    @staticmethod
    def locate_image(image):
        """
        This lets us pull images without post processing.
        """
        return 'img/base/' + file_rename(settings.theme + '_', image, reverse=True)


class Calibrations(Frame):
    """
    This is the machine calibration and configuration interface.
    """
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.send_command = self.controller.director.send_command
        self.send = self.controller.director.send
        self.command = self.controller.command
        self.settings = self.controller.settings
        self.remote_settings = None
        self.show_frame = self.controller.show_frame
        self.editvar = self.remote_settings
        self.rt_data = controller.rt_data
        self.temp = self.rt_data['temp']
        self.error_message = self.temp['error_message'] = StringVar()
        self.stagename = StringVar()
        self.stage_id = None
        self.stream_term = self.temp['datastream_term']
        self.stream_ready = False
        self.str_wdo = None
        self.stage_buttons = []
        self.target = self.controller.target
        self.dummy = None
        self.leg_util_frame = None
        #  ##############
        #  Configure base
        #  ##############
        self.base = Frame(
            self,
            bg=theme['main']
        )
        self.base.grid(row=0, column=0)
        center_weights(
            self.base,
            rows=3,
            cols=2
        )
        self.stage_title_frame = Frame(
            self.base,
            width=prx(23),
            height=pry(8)
        )
        self.stage_title_frame.grid(row=0, column=0)
        self.stage_title = config_text(
            Label(
                self.stage_title_frame,
            ),
            text='stage selection',
            pad=0
        )
        self.stage_title.pack()
        self.stage_selector = Frame(
            self.base,
            width=prx(23),
            height=pry(70),
            bg=theme['main']
        )
        self.stage_selector.grid(row=1, column=0)
        self.stage_list = VerticalScrolledFrame(self.stage_selector, width=prx(20), height=pry(75))
        self.stage_list.pack()
        self.list_stages = list_stages
        self.selected_stage_frame = Frame(
            self.base,
            width=prx(23),
            height=pry(4),
            bg=theme['main']
        )
        self.selected_stage_frame.grid(row=2, column=0)
        self.selected_stage = config_text(
            Label(
                self.selected_stage_frame,
            ),
            text=self.stagename,
            pad=0
        )
        self.selected_stage.pack()
        self.options = Frame(
            self.base,
            height=pry(88),
            bg=theme['main'],
        )
        self.options.grid(row=0, column=1, rowspan=3, sticky='nsew')
        center_weights(
            self.options,
            cols=4
        )
        # ###########
        # debug modes
        # ###########
        self.debug_title_frame = Frame(
            self.options,
            width=prx(23),
            height=pry(8)
        )
        self.debug_title_frame.grid(row=0, column=0)
        self.debug_title = config_text(
            Label(
                self.debug_title_frame,
            ),
            text='debug modes'
        )
        self.debug_title.pack()

        names = [
            'console',
            'stats',
            'PWM',
            'ADC',
            'PWM/ADC',
            'IMU/9DOF',
            'sonar'
        ]
        commands = [
            lambda: self.text(),
            lambda: self.stats(),
            lambda: self.pwm(),
            lambda: self.adc(),
            lambda: self.pwmadc(),
            lambda: self.gyro(),
            lambda: self.command_event('Calibrations', 'debug_mode("sonar")'),
        ]
        button_array(
            self.options,
            names,
            commands,
            rw=1,
            vert=True
        )
        # ###############
        # system commands
        # ###############
        self.sys_cmd_title_frame = Frame(
            self.options,
            width=prx(23),
            height=pry(10)
        )
        self.sys_cmd_title_frame.grid(row=0, column=1)
        self.sys_cmd_title = config_text(
            Label(
                self.sys_cmd_title_frame
            ),
            text='system commands'
        )
        self.sys_cmd_title.pack()

        names = [
            'reboot',
            'shutdown',
            'selftest',
            'wifi reset',
            'run command',
            'edit settings',
            'report',
        ]
        commands = [
            lambda: self.command_event('Calibrations', 'reboot()'),
            lambda: self.command_event('Calibrations', 'poweroff()'),
            lambda: self.command_event('Calibrations', 'selftest()'),
            lambda: self.command_event('Calibrations', 'network_reset()'),
            '',
            lambda: self.edit_setting(),
            ''
        ]
        button_array(
            self.options,
            names,
            commands,
            rw=1,
            col=1,
            vert=True
        )
        # ############
        # calibrations
        # ############
        self.calibrations_title_frame = Frame(
            self.options,
            width=prx(23),
            height=pry(8)
        )
        self.calibrations_title_frame.grid(row=0, column=2, columnspan=2)
        self.cal_title = config_text(
            Label(
                self.calibrations_title_frame,
            ),
            text='calibrations'
        )
        self.cal_title.pack()

        names = [
            'set gyros',
            'vision',
            'echolocation',
            'balance/accel',
            'speeds',
            'bounce',
            'physical'
        ]

        commands = [
            lambda: self.calibrate_gyros(),
            '',
            '',
            '',
            '',
            '',
            ''
        ]

        button_array(
            self.options,
            names,
            commands,
            rw=1,
            col=2,
            vert=True
        )

        names = [
            'gimbal',
            'timing',
            'feedback',
            'leg 1',
            'leg 2',
            'leg 3',
            'leg 4'
        ]

        commands = [
            lambda: self.command_event('Calibrations', 'jog_servo(\'LEG1\', \'x\')'),
            lambda: self.command_event('Calibrations', 'servo(0, -10)'),
            '',
            lambda q='LEG1': self.calibrate_leg(q),
            lambda q='LEG2': self.calibrate_leg(q),
            lambda q='LEG3': self.calibrate_leg(q),
            lambda q='LEG4': self.calibrate_leg(q)
        ]

        button_array(
            self.options,
            names,
            commands,
            rw=1,
            col=3,
            vert=True
        )

        # self.refresh()

    def close_streamer(self, container=None):
        """
        This destroys a streamer window and closes its thread.
        """
        self.stream_term = True
        if container:  # This allows us to clean up more complex stream windows.
            container.destroy()
        self.str_wdo.destroy()

    def text(self):
        """
        This allows us to view the remote console.

        TODO: These debugging states are expected to change in the future and have been left exploded for ease of editing.
        """
        if self.check_for_stage('Calibrations'):
            self.stream_term = False
            values = dict()
            for key in range(8):
                exec('values[\'s_' + str(key) + '\'] = StringVar()')
            self.str_wdo = stream_window(controller=self, parent=self.base, requested_data="['SUB_TEXT']",
                                         requested_cycletime=1, terminator=self.stream_term, target='Calibrations',
                                         varss=values, mode='text', command=lambda q=self: self.close_streamer())
            cparent(self.base, self.str_wdo)  # Center frame.

    def stats(self):
        """
        This will open a stats stream windows.
        """
        if self.check_for_stage('Calibrations'):
            self.stream_term = False
            values = dict()
            for key in range(8):
                exec('values[\'s_' + str(key + 1) + '\'] = StringVar()')
            self.str_wdo = stream_window(controller=self, parent=self.base, requested_data="['SUB_STATS']",
                                         requested_cycletime=1, terminator=self.stream_term, target='Calibrations',
                                         varss=values, mode='stats', command=lambda q=self: self.close_streamer())
            cparent(self.base, self.str_wdo)  # Center frame.

    def adc(self):
        """
        This will open a datastream showing the ADC activity.
        """
        if self.check_for_stage('Calibrations'):
            self.stream_term = False
            values = dict()
            for key in range(8):
                exec('values[\'s_' + str(key) + '\'] = StringVar()')
            self.str_wdo = stream_window(controller=self, parent=self.base, requested_data="['SUB_ADC']",
                                         requested_cycletime=0.05, terminator=self.stream_term, target='Calibrations',
                                         varss=values, mode='adc', command=lambda q=self: self.close_streamer())
            cparent(self.base, self.str_wdo)  # Center frame.

    def pwm(self):
        """
        This will open a datastream showing the ADC activity.
        """
        if self.check_for_stage('Calibrations'):
            self.stream_term = False
            values = dict()
            for key in range(8):
                exec('values[\'s_' + str(key) + '\'] = StringVar()')
            self.str_wdo = stream_window(controller=self, parent=self.base, requested_data="['SUB_PWM']",
                                         requested_cycletime=0.05, terminator=self.stream_term, target='Calibrations',
                                         varss=values, mode='pwm', command=lambda q=self: self.close_streamer())
            cparent(self.base, self.str_wdo)  # Center frame.

    def pwmadc(self):
        """
        This will open a datastream showing the ADC activity.
        """
        if self.check_for_stage('Calibrations'):
            self.stream_term = False
            values = dict()
            for key in range(8):
                exec('values[\'s_' + str(key) + '\'] = StringVar()')
            self.str_wdo = stream_window(controller=self, parent=self.base, requested_data="['SUB_PWMADC']",
                                         requested_cycletime=0.05, terminator=self.stream_term, target='Calibrations',
                                         varss=values, mode='pwmadc', command=lambda q=self: self.close_streamer())
            self.str_wdo.place(
                x=prx(25),
                y=pry(5)
            )

    def gyro(self):
        """
        This will open a datastream showing the ADC activity.
        """
        if self.check_for_stage('Calibrations'):
            self.stream_term = False
            values = dict()
            for key in range(8):
                exec('values[\'s_' + str(key) + '\'] = StringVar()')
            self.str_wdo = stream_window(controller=self, parent=self.base, requested_data="['SUB_GYRO']",
                                         requested_cycletime=0.05, terminator=self.stream_term, target='Calibrations',
                                         varss=values, mode='gyro', command=lambda q=self: self.close_streamer())
            cparent(self.base, self.str_wdo)  # Center frame.

    def calibrate_gyros(self):
        """
        This will open a datastream allowing for realtime monitoring of gyro calibration status
        """
        gyro_cal_frame = Frame(
            self.base,
            width=prx(42),
            height=pry(80),
            bg=theme['main'],
            highlightthickness=pry(1),
            highlightbackground=theme['entrybackground']
        )
        cparent(self.base, self.str_wdo)  # Center frame.
        if self.check_for_stage('Calibrations'):
            self.stream_term = False
            values = dict()
            for key in range(6):
                exec('values[\'s_' + str(key) + '\'] = StringVar()')
            self.str_wdo = stream_window(controller=self, parent=gyro_cal_frame,
                                         requested_data="['SUB_GYRO_CALIBRATE']", requested_cycletime=0.05,
                                         terminator=self.stream_term, target='Calibrations', varss=values,
                                         mode='gyro_calibrate',
                                         command=lambda q=self: self.close_streamer(gyro_cal_frame), no_border=True)
            self.str_wdo.grid(row=0, columnspan=3)
        labels = [
            'reset IMU',
            'save',
            'reset 9DOF',
        ]
        commands = [
            lambda: self.command_event(self.stage_id, 'reset_imu()'),
            lambda: self.command_event(self.stage_id, 'settings_save()'),
            lambda: self.command_event(self.stage_id, 'reset_gyro()')
        ]
        button_array(
            gyro_cal_frame,
            labels,
            commands,
            rw=1,
            # vert=True
        )

    def check_for_stage(self, target=None):
        """
        This checks that we have a stage selected, if not shows an error.

        In the event of an error we will raise the error frame and return to the element specified
        in the target variable when closed.
        """
        if not target:
            target = self.controller.target
        result = False
        if self.stagename and self.stage_id:
            result = True
        else:
            self.controller.target = target
            self.controller.temp['error_message'].set('please select a stage')
            self.controller.show_frame('ErrorWidget')
        return result

    def refresh(self, page=None):
        """
        This will refresh our stage related data.
        """
        self.list_stages(self, self.stage_list)
        if page:
            self.controller.refresh(page)
        # if self.stage_id:  # We may need to move this.
        #     self.refresh_remote_settings()

    def command_event(self, target, command):
        """
        This issues a command to the selected stage. will show an error if no stage is selected.
        """
        if self.check_for_stage(target):
            self.send_command(self.stage_id, command)

    def edit_setting(self):
        """
        This will launch the settings editor.
        """
        if self.check_for_stage('Calibrations'):
            self.refresh_remote_settings()
            self.editvar = self.remote_settings
            Editor(self.base, self)

    def refresh_remote_settings(self):
        """
        This will grab our remote settings from the selected stage.
        """
        self.command_event('Calibrations', 'send_settings()')
        self.remote_settings = None
        rty = 0
        while not self.remote_settings and rty < 5:
            time.sleep(1)
            try:
                self.editvar = self.remote_settings = self.rt_data['LISTENER'][self.stage_id]['SETTINGS']
                print(self.editvar['role'])
            except KeyError:
                rty += 1
        # print(self.rt_data)

    def axis_mover(self, parent, grid, channel):
        """
        This will present us with a widget allowing for the manual movement of a single axis.
        """
        rw, cl, sp = grid
        self.dummy = channel
        mover_frame = Frame(
            parent
        )
        channel = str(channel)
        mover_frame.grid(row=rw, column=cl, columnspan=sp)
        names = ['-50', '-10', '-1', '+1', '+10', '+50']
        commands = list()
        for name in names:
            name = name.replace('+', '')
            commands.append(lambda q=channel, u=name: self.command_event('Calibrations', 'servo(' + q + ', ' + u + ')'))
        button_array(
            mover_frame,
            names,
            commands,
            size=(5, 10),
            aspect=False
        )
        return mover_frame

    # noinspection PyDefaultArgument
    def set_limits(self, parent, legs, leg_id, axis):
        """
        This will present us with a series of options to explore and record the minimum, maximum and neutral
        positions of a given axis.
        """
        def save(slf, _parent):
            """
            This saves the leg settings and closes the dialog.
            """
            slf.command_event('Calibrations', 'settings_save()')
            slf.command_event('Calibrations', 'send_settings()')
            _parent.destroy()

        def lock(slf, _leg_id, _axis, _name):
            """
            This will lock in an axis limit.
            """
            slf.command_event('Calibrations', 'lock_limit(' + _leg_id + ', ' + _name + ', ' + _axis + ')')
        leg = legs[leg_id]
        limits_frame = Frame(
            parent
        )
        names = ['cancel', 'lock\nmin', 'lock\nmax', 'lock\nneutral', 'reverse', 'save']
        lid = sq(leg_id)
        ax = sq(axis)
        commands = [
            lambda: limits_frame.destroy(),
            lambda: lock(self, lid, ax, sq('min')),
            lambda: lock(self, lid, ax, sq('max')),
            lambda: lock(self, lid, ax, sq('nu')),
            lambda: self.command_event('Calibrations', 'reverse_axis(\'' + str(leg[axis]['pwm']) + '\')'),
            lambda a=limits_frame: save(self, a)
        ]
        button_array(
            limits_frame,
            names,
            commands,
            size=(5, 10),
            aspect=False
        )
        self.axis_mover(
            limits_frame,
            (1, 0, 6,),
            leg[axis]['pwm']
        )
        cparent(
            parent,
            limits_frame
        )
        return limits_frame

    def channel_selector(self, parent, legs, leg_id):
        """
        This will produce a widget that allows us to set PWM and ADC channel mappings.
        """
        self.dummy = None
        leg = legs[leg_id]
        x_p, x_a = leg['x']['pwm'], leg['x']['adc']
        y_p, y_a = leg['y']['pwm'], leg['y']['adc']
        z_p, z_a = leg['z']['pwm'], leg['z']['adc']
        f_a = leg['foot']['adc']
        channel_pwm_vars = [miv(x_p), miv(y_p), miv(z_p)]
        channel_pwm_coms = [
            '',
            '',
            ''
        ]
        channel_adc_vars = [miv(x_a), miv(y_a), miv(z_a), miv(f_a)]
        channel_adc_coms = [
            '',
            '',
            '',
            ''
        ]
        channel_name_vars = ['ϕ phi X: PWM / ADC', 'θ theta Y: PWM / ADC', 'ρ rho Z: PWM / ADC', 'foot ADC']
        channel_name_coms = [
            '',
            '',
            '',
            ''
        ]
        channel_frame = Frame(
            parent,
            bg=theme['main']
        )
        names = ['cancel', 'save']
        commands = [
            lambda: channel_frame.destroy(),
            ''
        ]
        options_frame = Frame(
            channel_frame,
            bg=theme['main']
        )
        options_frame.grid(row=0, column=0, columnspan=3)
        button_array(
            options_frame,
            names,
            commands
        )
        button_array(
            channel_frame,
            channel_name_vars,
            channel_name_coms,
            rw=1,
            vert=True,
            size=(1.6, 0),
            label=True
        )
        button_array(
            channel_frame,
            channel_pwm_vars,
            channel_pwm_coms,
            rw=1,
            col=1,
            vert=True,
            size=(5, 10),
            aspect=False
        )
        button_array(
            channel_frame,
            channel_adc_vars,
            channel_adc_coms,
            rw=1,
            col=2,
            vert=True,
            size=(5, 10),
            aspect=False
        )
        cparent(
            parent,
            channel_frame
        )

    def calibrate_leg(self, leg_id):
        """
        This is where we will set leg pinnings, min/max range of motion, gravity neutral, along with
            ADC values by range.

        NOTE: This is going to be one of the more involved calibration utilities as it will span the operation
                of most of the various phisical control hardware.

        TODO: We need to keep saftey in mind here, we don't want to cause physical damage to the machine.

        Functions:
        move per axis in increments of 1, 10, 50,
        Jog per axis,
        set max / neutral / min per axis.
        Reverse axis,
        Discover ADC values per-step (maybe)
        Set PWM and ADC channels per axis.
        Render local grid (Enhancement)
        """
        if self.leg_util_frame:
            self.leg_util_frame.destroy()
        if self.check_for_stage('Calibrations'):
            self.refresh_remote_settings()
            legs = eval(self.remote_settings['legs'])  # Remember we will have to convert this back into a string when we save.
            leg = legs[leg_id]
            print(leg)
            self.leg_util_frame = Frame(
                self.base,
                width=prx(50),
                height=pry(89),
                bg=theme['main'],
            )
            # Remember we have to center the child after we fill out it's contents.

            center_weights(self.leg_util_frame)
            # ##########
            # Left panel
            # ##########
            left_panel = Frame(
                self.leg_util_frame,
                width=prx(22),
                height=pry(84),
                bg=theme['main'],
            )
            left_panel.grid(row=0, column=0)
            names = [
                'cancel',
                'set channels',
                'jog ρ rho Z',
                'jog θ theta Y',
                'jog ϕ phi X',
                'save'
            ]
            commands = [
                lambda: self.leg_util_frame.destroy(),
                lambda: self.channel_selector(self.leg_util_frame, legs, leg_id),
                lambda li=leg_id: self.command_event('Calibrations', 'jog_servo(\'' + li + '\', \'z\')'),
                lambda li=leg_id: self.command_event('Calibrations', 'jog_servo(\'' + li + '\', \'y\')'),
                lambda li=leg_id: self.command_event('Calibrations', 'jog_servo(\'' + li + '\', \'x\')'),
                '',
            ]
            button_array(
                left_panel,
                names,
                commands,
                # rw=0,
                vert=True
            )
            # #######
            # Diagram
            # #######
            image_panel = Frame(
                self.leg_util_frame,
                width=prx(22),
                height=pry(65),
                bg=theme['main'],
            )
            image_panel.grid(row=0, column=1)
            if leg_id in ['LEG1', 'LEG3']:
                file = 'leg13.png'
            else:
                file = 'leg24.png'
            leg_diagram = PhotoImage(file=img(file, 22, 65))
            leg_diagram_label = Label(
                image_panel,
                bg=theme['main'],
                width=prx(22),
                height=pry(75),
                image=leg_diagram,
            )
            leg_diagram_label.image = leg_diagram
            leg_diagram_label.pack(fill="both", expand=True)
            # ###########
            # Right panel
            # ###########
            right_panel = Frame(
                self.leg_util_frame,
                width=prx(22),
                height=pry(84),
                bg=theme['main']
            )
            right_panel.grid(row=0, column=3)
            names = [
                'set ρ rho Z limits',
                'set θ theta Y limits',
                'set ϕ phi X limits',
                'train ρ rho Z dist',
                'train θ theta Y yaw',
                'train ϕ phi X pitch',
                'render local grids',
            ]
            q = (self.leg_util_frame, legs, leg_id)
            commands = [
                lambda u='z': self.set_limits(*q, u),
                lambda u='y': self.set_limits(*q, u),
                lambda u='x': self.set_limits(*q, u),
                '',
                '',
                '',
            ]
            button_array(
                right_panel,
                names,
                commands,
                vert=True,
                size=(15, 10),
                aspect=False
            )
            cparent(
                self.base,
                self.leg_util_frame
            )


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
        self.temp = self.rt_data['temp'] = dict()
        self.settings = settings
        self.defaults = self.settings.defaults
        for sett in self.defaults:  # Populate defaults
            self.rt_data[sett] = StringVar()
            self.rt_data[sett].set(str(self.defaults[sett]))
        self.editvar = self.settings.settings
        self.target = self.temp['targetframe'] = 'Writer'  # This is the page we will raise after a widget is closed.
        self.entertext = self.temp['entertext'] = 'enter'
        self.stagedata = self.temp['stagedata'] = dict()
        self.stagetarget = self.temp['stagetarget'] = str()
        self.stage = None
        self.datastream_term = self.temp['datastream_term'] = False
        self.rehersals = rt_data['rehearsals'] = settings.rehearsals
        self.num_max = 100  # Maximum default number for the num pad.
        self.scripts = rt_data['scripts'] = settings.scripts
        self.has_plot = False
        self.command = None
        self.notification = StringVar()
        self.notification_timeout = IntVar()
        self.notification_timeout.set(self.settings.notification_timeout)
        self.rt_data['key_test'] = StringVar()  # TODO: This is just for testing the keyboard.
        self.rt_data['key_test'].set('')
        self.spacer = get_spacer()
        self.update()  # I wish I had thought of this sooner...
        from director.rt import Start  # Attempts to keep ourselves somewhat thread safe...
        self.director = Start(self)  # online director.

        container = tk.Frame(self)
        container.place(
            x=0,
            y=0,
            width=scr_x,
            height=scr_y
        )
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.container = container
        self.frames = dict()
        # self.refresh()
        for F in (  # Ensure the primary classes are passed before the widgets.
                Home,
                Writer,
                Audience,
                Rehearsal,
                Calibrations,
                Keyboard,
                NumPad,
                FileBrowser,
                CloseWidget,
                QRCodeWidget,
                LoadingIcon,
                ConfirmationWidget,
                ErrorWidget
        ):  # TODO: This is pretty messy and should be cleaned up after we know what all this looks like.
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            if page_name == 'NumPad':
                frame.configure(
                    height=pry(50),
                    width=pry(50),
                    bg=theme['entrybackground'],
                    borderwidth=pry(1),
                )
                frame.grid(row=0, column=0)
            elif page_name == 'Keyboard':
                frame.configure(
                    height=pry(70),
                    width=scr_x,
                    bg=theme['entrybackground'],
                    borderwidth=pry(1)
                )
                frame.grid(row=0, column=0, sticky=S)
            elif page_name == 'FileBrowser':
                frame.configure(
                    height=pry(73),
                    width=pry(43),
                    bg=theme['entrybackground'],
                    borderwidth=pry(1),
                    highlightbackground=theme['entrybackground']
                )
                frame.grid(row=0, column=0)
            elif page_name == 'CloseWidget':
                frame.configure(
                    height=(pry(18)),
                    width=(prx(10)),
                )
                frame.grid(row=0, column=0, sticky=NW)
            elif page_name == 'QRCodeWidget':
                frame.configure(
                    height=pry(90),
                    width=pry(90),
                    bg='white'
                )
                frame.grid(row=0, column=0)
            elif page_name == 'LoadingIcon':
                frame.configure(
                    height=prx(15),
                    width=pry(15),
                    bg=theme['main']
                )
                frame.grid(row=0, column=0)
            elif page_name == 'Rehearsal':
                frame.configure(
                    height=pry(96),
                    width=prx(71),
                    bg=theme['main'],
                    highlightthickness=pry(1),
                    highlightbackground=theme['entrybackground']
                )
                frame.grid(row=0, column=0)
            elif page_name == 'Calibrations':
                frame.configure(
                    width=prx(71),
                    height=pry(91),
                    bg=theme['main'],
                    highlightthickness=pry(1),
                    highlightbackground=theme['entrybackground']
                )
                frame.grid(row=0, column=0)
            elif page_name == 'ConfirmationWidget' or page_name == 'ErrorWidget':
                frame.configure(
                    width=prx(30),
                    height=pry(30),
                    highlightthickness=pry(1),
                    highlightbackground=theme['entrybackground']
                )
                frame.grid(row=0, column=0)
            else:
                frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame('Home')
        self.notify('online successful')

    def get_frame(self, page_name):
        """
        This fetches the target frame.
        """
        return self.frames[page_name]

    def show_frame(self, page_name):
        """
        Shows a frame...
        """
        if isinstance(page_name, list):
            for f in page_name:
                self.get_frame(f).tkraise()
        else:
            frame = self.get_frame(page_name)
            frame.tkraise()

    def refresh(self, page_name):
        """
        We can use this to refresh the target frame.
        """
        frame = self.get_frame(page_name)
        frame.refresh()

    def clear(self, page_name):
        """
        This triggers a page to clear or refresh contents.
        """
        frame = self.get_frame(page_name)
        frame.clear()

    def update(self):
        """
        This updates the controller with all the new values in the real time data model.
        """
        for setting in self.rt_data:
            exec('self.' + setting + ' = self.rt_data[setting]')

    def notify(self, message=None):
        """
        This raises a notification dialog.
        """
        self.notification_timeout.set(self.settings.notification_timeout)
        if message:
            self.notification.set(message)
        timed_element(
            self.container,
            self,
            Notifier,
            self.notification_timeout
        )


class Editor(Frame):
    """
    This is our file editor widget.
    """
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.settings = self.controller.settings
        self.rt_data = self.controller.rt_data
        self.temp = self.rt_data['temp']
        self.stage_id = self.controller.stage_id
        self.send = self.controller.send
        self.command = None
        self.command_event = controller.command_event
        self.show_frame = self.controller.show_frame
        self.target = self.controller.target
        self.def_text = self.temp['default_keyboard_text']
        self.def_val = ''
        self.rt_data['edit'] = StringVar()  # Set pickup variable.
        self.editvar = self.controller.editvar
        self.buttons = dict()
        self.rename = None
        self.var = None
        self.title = StringVar()
        self.title.set('cancel')
        # ##############
        # Configure base
        # ##############
        self.base = Frame(
            parent,
            width=prx(75),
            height=pry(80),
            bg=theme['entrybackground'],
            borderwidth=pry(1),
        )
        # self.base.place(
        #     x=cp(prx(37.5), prx(40)),
        #     y=0
        # )
        self.refresh()
        cparent(parent, self.base)  # Center frame.

    def exit(self):
        """
        This kills our widget.
        """
        SaveRemoteSettings(self)  # Save remote settings.
        self.controller.target = ['Writer', 'CloseWidget']  # Set target for closure raise.
        self.base.destroy()  # Destroy widget.

    def refresh(self):
        """
        This re-creates the editor, updating it's contents.
        """
        # self.exit()
        self.add_scroller(var=self.editvar)

    @staticmethod
    def create_text(item, value):
        """
        This just returns a text var from whatever type we send.
        """
        text = StringVar()
        try:
            value = eval(value)
        except (NameError, SyntaxError):
            pass
        if isinstance(value, str):
            text.set(item + ' = ' + value)
        elif isinstance(value, int) or isinstance(value, float):
            text.set(item + ' = ' + str(value))
        elif isinstance(value, list) or isinstance(value, dict) or isinstance(value, tuple):
            text.set(item + '= ...')
        return text

    def edit(self, def_text='', def_val='', col=0):
        """
        This will raise a keyboard allowing for an item to be altered.

        TODO: THis will be passed to the list buttons.
        """
        # print('def_text', def_text)
        self.def_text.set(def_text)  # Set default keyboard text.
        self.def_val = def_val
        self.temp['default_keyboard_text'].set(def_text)
        self.temp['word'].set('edit')  # Define out pickup variable.
        # self.controller.command = self.edit_event()  # Set keyboard command event.
        ctrl = self.controller.controller
        ctrl.target = ['Writer', 'Calibrations', 'CloseWidget']  # Set frame raise sequence.
        ctrl.command = lambda q=col: self.edit_event(q)
        ctrl.refresh('Keyboard')
        ctrl.show_frame('Keyboard')  # Show keyboard.

    def edit_event(self, col):
        """
        This will save the items new value.

        TODO: This will be passed to the keyboard widget and triggered on save.
        """
        value = self.rt_data['edit'].get()
        if not col:
            setting = self.def_val
            if self.def_val:
                self.editvar[setting] = value
                self.refresh()
                self.title.set('save')
        ctrl = self.controller.controller
        ctrl.target = ['Writer', 'CloseWidget']  # Set frame raise sequence.
        return self

    @staticmethod
    def back_event(col):
        """
        This destroys a sub-scroller.
        """
        exec('self.scroller_' + str(col) + '.destroy()')

    def add_edit_button(self, parent, buttons, text, command=None):
        """
        This adds a button to our editor.
        """
        buttons.append(
            self.add_button(
                parent,
                text,
                command
            )
        )
        buttons[-1].pack()
        return buttons

    @staticmethod
    def add_button(parent, text, command=None, size=2):
        """
        This will add a single unpacked edit button.
        """
        return config_editor_button(
            Button(
                parent,
                command=command
            ),
            text=text,
            size=size,
            width=30
        )

    def add_child_scroller(self, col, var):
        """
        This will open a sub-scroller so we can edit inside dicts and arrays.
        """
        self.add_scroller(col, var)

    def add_scroller(self, col=0, var=None):
        """
        This will ad a vertical scroll window to the settings selection screen.
        TODO: we probably want to change this to a placement instead of grid.

        TODO: Add functionality for child_arrays/dicts

        NOTE: Editing within arrays and dicts is disabled for now as I haven't found a good way to handle that.
        """
        self.var = var
        # print(var)
        key = str(col)
        if key not in self.buttons.keys():  # Confirm we have an array.
            self.buttons[key] = list()
        else:
            for button in self.buttons[key]:  # If there are old buttons destroy them.
                button.destroy()
        self.buttons[key + '_values'] = dict()
        buttons = self.buttons[key]
        textvars = self.buttons[key + '_values']
        scroll_frame = Frame(
            self.base,
            width=prx(30),
            height=pry(80),
            bg=theme['main'],
        )
        save_button_frame = Frame(
            scroll_frame,
            width=prx(30),
            bg=theme['entrybackground'],
            bd=1
        )
        save_button_frame.grid(row=0, column=0)
        center_weights(save_button_frame)
        if not col:
            save_button = self.add_button(  # Add save button.
                save_button_frame,
                self.title,
                lambda: self.exit(),
                size=4
            )
        else:
            save_button = self.add_button(  # Add save button.
                save_button_frame,
                'back',
                lambda q=col: self.back_event(q),
                size=4
            )
        save_button.configure(
            anchor=CENTER,
        )
        save_button.pack()
        scroll_frame.grid(row=0, column=0)
        scroller = VerticalScrolledFrame(scroll_frame, prx(30), pry(80))
        scroller.grid(row=1, column=col)
        for item in var:  # Add editor configuration lines.
            value = var[item]
            text = self.create_text(item, value)
            if '...' not in text.get():  # Check for child array.
                buttons = self.add_edit_button(
                    scroller.interior,
                    buttons,
                    text,
                    lambda q=value, w=item, r=col: self.edit(def_text=q, def_val=w, col=r),  # Add normal edit button.
                )
            # else:
            #     buttons = self.add_edit_button(
            #         scroller.interior,
            #         buttons,
            #         text,
            #         lambda q=(col + 1), w=eval(value): self.add_child_scroller(col=q, var=w),  # Add sub-key edit button.
            #     )
            textvars[item] = text
        exec('self.scroller_' + str(col) + ' = scroller')


class Notifier(Frame):
    """
    This pops upa notification at the top of the screen.
    """
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.controller.refresh('Rehearsal')
        self.controller.refresh('Calibrations')
        self.message = self.controller.notification  # Pull message from controller.
        self.target = self.controller.target  # Find out where we are going to revert to.
        self.base = Frame(
            parent,
            width=prx(50),
            height=pry(5),
        )
        self.base.place(
            x=cp(prx(50), prx(50)),
            y=0
        )
        self.im = img('notifier.png', 50, 5, aspect=False)
        self.img = PhotoImage(file=self.im)
        self.btn = config_button(
            Button(
                self.base,
                width=prx(50),
                height=pry(5),
                image=self.img,
                textvariable=self.message,
                command=lambda: self.destroy()
            )
        )
        self.btn.configure(fg='white')
        self.btn.image = self.im
        self.btn.pack()
        self.base.tkraise()
        # print('notifying')

    def destroy(self):
        """
        This causes the notifier to destroy itself so we can re_use it later.
        """
        # print('destroying')
        self.btn.destroy()
        self.base.destroy()
        # self.controller.show_frame(self.target)


class NumPad(Frame):
    """
    Creates a simple number pad.
    """

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        global rt_data
        self.controller = controller
        self.rt_data = rt_data
        self.target = controller.target
        self.temp = self.rt_data['temp']
        self.model = parent
        self.controller = controller
        self.grid()
        self.numvar = StringVar()
        self.numvar.set('')
        self.entvar = StringVar()
        self.entvar.set('')
        # print(self.numvar.get())
        self.get_num()
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
        Sets or updates the number variable.
        """
        number = str(number)
        if self.number:
            self.number += number
        else:
            self.number = number
        self.numvar.set(self.number)
        self.ent_go()

    def pass_nums(self):
        """
        This passes our numbers to the parent model.
        """
        # print(self.numvar.get())
        if self.numvar.get():  # Prevent returning nulls.
            num = int(self.numvar.get())
            if num > self.controller.num_max:
                num = str(self.controller.num_max)
            self.get_num().set(num)
            self.temp['number'].set('0')
        self.controller.show_frame(self.controller.target)
        self.numvar.set('')
        self.number = None
        if self.controller.command:
            self.controller.command()  # Execute optional command.

    def delete_nums(self):
        """
        Removes the last number entered.
        """
        self.number = self.number[0:-1]
        self.numvar.set(self.number)
        self.ent_go()

    def numpad_create(self):
        """
        Creates a simple number pad.
        """
        self.ent_go()
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
            self.b = Button(self, text=b, width=width, height=height, command=lambda q=b: self.set_num(q))
            config_number_button(self.b)
            self.b.grid(row=r, column=c)
            c += 1
            if c > 2:
                c = 0
                r += 1
        self.dell = Button(self, text='del', width=width, height=height, command=lambda: self.delete_nums())
        config_number_button(self.dell)
        self.dell.grid(row=4, column=1)
        self.go = Button(self, textvariable=self.entvar, width=width, height=height, command=lambda: self.pass_nums())
        config_number_button(self.go)
        self.go.grid(row=4, column=2)

    def ent_go(self):
        """
        This changes the text on our enter button.
        """
        print(self.numvar.get())
        if self.numvar.get():
            self.entvar.set('go')
        else:
            self.entvar.set('exit')


class Keyboard(Frame):
    """
    Virtual Keyboard.

    TODO: Insure to create parent, controller and default text passage in the INIT statement.
    TODO: Now that i think about it we are gonna have to pass that through the real time model...
    """

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        global rt_data
        self.rt_data = rt_data
        self.controller = controller
        self.temp = self.rt_data['temp']
        self.temp['default_keyboard_text'] = StringVar()
        self.target = self.controller.target
        self.wordvar = StringVar()
        self.wordvar.set('')
        self.word = ''
        self.controller = controller
        self.stringvars = list()
        self.keys_lower = list()
        self.default_keys = [
            [
                [
                    "Character_Keys",
                    ({'side': 'top', 'expand': 'yes', 'fill': 'both'}),
                    [
                        ('`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', '\\', 'del'),
                        ('q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']'),
                        ('a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", self.controller.entertext),
                        ('z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/'),
                        ('caps', '\t\tspace\t\t')
                    ]
                ]
            ]
        ]
        self.keys_upper = [
            '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '|',
            'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}',
            'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"',
            'Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?'
        ]

        self.create_frames_and_buttons()

    def create_frames_and_buttons(self):
        """
        Loop to create keys.
        """
        for key_section in self.default_keys:  # create Sperate Frame For Every Section
            store_section = Frame(self, bg=theme['main'])
            store_section.pack(side='left', expand='yes', fill='both')
            for layer_name, layer_properties, layer_keys in key_section:
                store_layer = LabelFrame(store_section)
                store_layer.configure(bg=theme['main'])
                store_layer.pack(layer_properties)
                input_frame = Frame(store_layer)  # Create input label.
                input_frame.pack(side='top', expand='yes', fill='both')
                input_label = Label(
                    input_frame,
                    textvariable=self.wordvar,
                    bg=theme['main'],
                    fg=theme['buttontext'],
                    font=(theme['font'], str(pointsy(5)))
                )
                input_label.pack(side='top', expand='yes', fill='both')
                for key_bunch in layer_keys:
                    store_key_frame = Frame(store_layer)
                    store_key_frame.pack(side='top', expand='yes', fill='both')
                    for k in key_bunch:
                        txt = StringVar()
                        if len(k.strip()) < 3:
                            txt.set(k)
                            store_button = Button(store_key_frame, textvariable=txt, width=2, height=2)
                            self.stringvars.append(txt)
                            self.keys_lower.append(k)
                        else:
                            txt.set(k.center(5, ' '))
                            store_button = Button(store_key_frame, textvariable=txt, height=2)
                        if " " in k:
                            store_button['state'] = 'disable'
                        config_word_button(store_button)
                        store_button['command'] = lambda q=txt: self.button_command(q)
                        store_button.pack(side='left', fill='both', expand='yes')

    def button_command(self, event):
        """
        This is where we will insert the button events.
        """

        def switch_case(keys, varss):
            """
            Changes the case of the passed variables.
            """
            for lab, var in zip(keys, varss):
                var.set(lab)

        ename = event.get().strip()
        if ename == 'caps':
            switch_case(self.keys_upper, self.stringvars)
            event.set('lower')
        elif ename == 'lower':
            switch_case(self.keys_lower, self.stringvars)
            event.set('caps')
        elif ename == 'del':
            self.word = self.word[0:-1]
        elif ename == 'space':
            self.word += ' '
        elif ename == 'enter':
            print('enter command!', self.word)
            self.pass_word()
        else:
            self.word += event.get()
        self.wordvar.set(self.word)
        return event

    def get_word(self):
        """
        This fetches the target word stringvar from the rt_data.
        :rtype: StringVar
        """
        return self.rt_data[self.temp['word'].get()]

    def set_word(self, word):
        """
        Sets or updates the word variable.
        """
        if self.word:
            self.word += word
        else:
            self.word = word
            self.wordvar.set(self.word)

    def pass_word(self):
        """
        This passes our words to the parent model
        """
        if self.wordvar.get():  # Prevent returning nulls.
            self.get_word().set(self.wordvar.get())
            self.temp['number'].set('0')
        print('raising target', self.controller.target)
        self.controller.show_frame(self.controller.target)  # Im wondering if this need to be at the end...
        self.wordvar.set('')
        self.word = ''
        if self.controller.command:
            self.controller.command()
            self.controller.command = None

    def refresh(self):
        """
        Acquires a default text value.
        """
        if self.temp['default_keyboard_text'].get():
            self.word = self.temp['default_keyboard_text'].get()
            self.wordvar.set(self.word)


class FileBrowser(Frame):
    """
    This is a pretty cute touch oriented file browser.

    """

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        global rt_data
        self.rt_data = rt_data
        self.temp = rt_data['temp']
        self.controller = controller
        self.frame = VerticalScrolledFrame(self)  # Change this to get the lifting right.
        self.frame.pack()
        self.target = controller.target
        self.buttons = list()
        self.ext = self.temp['ext']
        self.dir = self.temp['folder']
        self.bad = True  # Toggle grey-out of wrong file types.
        if not self.ext:
            self.bad = False
        self.list_dirs()

    def list_dirs(self):
        """
        This will list the files and folder under the self.dir path.
        """
        self.ext = self.temp['ext']
        self.dir = self.temp['folder']
        self.buttons.append(
            config_file_button(
                Button(self.frame.interior, text='...', command=lambda: self.up_event())
            )
        )
        if not self.bad:
            self.buttons.append(
                config_file_button(
                    Button(self.frame.interior, text='< select folder >', command=lambda: self.up_event())
                )
            )

        self.buttons[-1].pack()
        files = os.listdir(self.dir)
        for i in files:
            if os.path.isdir(self.dir + i):
                self.buttons.append(
                    config_file_button(
                        Button(self.frame.interior, text=i + '/', command=lambda q=i: self.folder_event(q)))
                )
            else:
                if i[-4:] == self.ext:
                    self.buttons.append(
                        config_file_button(
                            Button(self.frame.interior, text=i, command=lambda q=i: self.select_event(q)))
                    )
                else:
                    if self.bad:
                        self.buttons.append(
                            config_file_button(Label(self.frame.interior, text=i), True)
                        )
                    else:
                        self.buttons.append(
                            config_file_button(
                                Button(self.frame.interior, text=i, command=lambda q=i: self.select_event(q)))
                        )

            self.buttons[-1].pack()

    def clear(self):
        """
        This clears the contents of the scroll window
        """
        for button in self.buttons:
            button.destroy()
            del button
        self.frame.reset()

        self.list_dirs()

    def folder_event(self, folder):
        """
        This will drop us into a folder on selection.
        """
        self.temp['folder'] += folder + '/'
        self.clear()

    def up_event(self):
        """
        This will take us up one folder level.
        """
        self.temp['folder'] = '/' + self.temp['folder'].split('/', 1)[-1].rsplit('/', 2)[0] + '/'
        self.clear()

    def select_event(self, filename):
        """
        This will pass the filename variable into realtime data and drop the browser frame.

        TODO: When we want to perform a file-save operation we will set the ext variable to not-true.
        """
        if self.ext:
            self.temp['targetfile'].set(self.temp['folder'] + '/' + filename)  # Build full path.
            self.controller.show_frame(self.target)  # Set global target file.
        else:
            self.controller.entertext = 'save'
            self.controller.show_frame('Keyboard')
            print('Save file logic here!')


class VerticalScrolledFrame(Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """

    def __init__(self, parent, width=None, height=None):
        Frame.__init__(self, parent)

        # create a canvas object and a vertical scrollbar for scrolling it
        self.canvasheight = pry(70)
        self.canvaswidth = pry(40)

        if width and height:
            self.canvas = canvas = Canvas(
                self,
                bg=theme['main'],
                height=height,
                width=width,
                highlightthickness=0,  # This is the secret to getting rid of that nasty border!
            )
        else:
            self.canvas = canvas = Canvas(
                self,
                bg=theme['main'],
                height=self.canvasheight,
                highlightthickness=0,  # This is the secret to getting rid of that nasty border!
            )
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)

        # reset the view
        self.reset()

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas, height=self.canvasheight, width=self.canvaswidth)
        self.interior.configure(
            bg=theme['main'],
            bd=0
        )
        # We create a dummy label here to control the width.
        # TODO: This fixes the visual aspect, but seems to break the 'click' command...
        spacr = get_spacer()
        self.block = Label(
            self.interior,
            bg=theme['main'],
            image=spacr,
            width=width,
            text='none'
        )
        self.block.image = spacr
        self.block.pack()
        self.interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            self.event = event
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() > canvas.winfo_width():  # Changed from neq to less than.
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
            elif interior.winfo_reqwidth() > canvas.winfo_width():
                interior.configure(width=canvas.winfo_width())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            self.event = event
            if interior.winfo_reqwidth() < canvas.winfo_width():  # Changes from neq to less than.
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(self.interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)

        self.offset_y = 0
        self.prevy = 0
        self.scrollposition = 1

        def on_press(event):
            """
            On press event.
            """
            self.offset_y = event.y_root
            if self.scrollposition < 1:
                self.scrollposition = 1
            elif self.scrollposition > self.canvasheight:
                self.scrollposition = self.canvasheight
            try:
                canvas.yview_moveto(self.scrollposition / self.canvasheight)
            except TclError:
                print('on press movement invalid.')
                pass

        def on_touch_scroll(event):
            """
            On scroll event.
            """
            nowy = event.y_root

            sectionmoved = settings.scroll_speed  # Adjust scroll speed.
            if nowy > self.prevy:
                event.delta = -sectionmoved
            elif nowy < self.prevy:
                event.delta = sectionmoved
            else:
                event.delta = 0
            self.prevy = nowy

            self.scrollposition += event.delta
            try:
                canvas.yview_moveto(self.scrollposition / self.canvasheight)
            except TclError:
                print('scroll movement invalid.')
                pass

        self.bind("<Enter>", lambda _: self.bind_all('<Button-1>', on_press), '+')
        self.bind("<Leave>", lambda _: self.unbind_all('<Button-1>'), '+')
        self.bind("<Enter>", lambda _: self.bind_all('<B1-Motion>', on_touch_scroll), '+')
        self.bind("<Leave>", lambda _: self.unbind_all('<B1-Motion>'), '+')

    def reset(self):
        """
        resets the canvas position.
        """
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def clear(self):
        """
        This clears the interior.
        """
        self.interior.pack_forget()
        self.reset()


class CloseWidget(Frame):
    """
    This is the object we will call to offer to drop a widget and raise the target frame.
    """

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.rt_data = self.controller.rt_data
        self.temp = self.controller.temp
        x = pry(20)
        y = pry(18)
        image = PhotoImage(file=img('close.png', 10, 10))
        self.close_button_frame = Frame(
            self,
            height=y,
            width=x
        )
        self.close_button_frame.grid(row=0, column=0)
        self.close_button = Button(
            self.close_button_frame,
            height=y,
            width=x,
            image=image,
            command=lambda: self.drop_event(),
        )
        self.close_button.image = image
        config_button(self.close_button)
        self.close_button.pack()

    def drop_event(self):
        """
        This will raise the target frame hiding whatever widget is currently in focus.
        """
        self.controller.show_frame(self.controller.target)
        print('raising:', self.controller.target)

    def show(self):
        """
        This allows us to raise the close button widget from a parent.
        """
        self.tkraise()


class ConfirmationWidget(Frame):
    """
    This presents a confirmation dialog sporting a confirm or cancel.
    """

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.rt_data = self.controller.rt_data
        self.temp = self.controller.temp
        self.confirmation_message = self.temp['confirmation_message'] = StringVar()
        self.confirmation_message.set('No Message loooooong test')
        self.base = Frame(
            self,
            bg=theme['main'],
            width=prx(30),
            height=pry(30)
        )
        self.base.grid(row=0, column=0)
        self.confirmation_message_frame = Frame(
            self.base,
            width=prx(30),
            height=pry(15),
            # bg='red'
        )
        self.confirmation_message_frame.grid(row=0, columnspan=2)
        self.confirmation_message_label = Label(
            self.confirmation_message_frame,
            textvariable=self.confirmation_message,
            width=prx(30),
            height=pry(15),
            image=get_spacer(),
            bg=theme['main'],
            fg=theme['buttontext'],
            compound=CENTER,
            font=(theme['font'], str(pointsy(3))),
            wraplength=pry(29)
        )
        self.confirmation_message_label.pack()
        button_array(
            self.base,
            ['confirm', 'cancel'],
            [
                self.confirm_event,
                self.cancel_event
            ],
            1,
        )

    def confirm_event(self):
        """
        This is our confirmation event that will execute the global command and raise the global target frame.
        """
        if self.controller.command:
            self.controller.command()
        self.clear()

    def cancel_event(self):
        """
        This cancels the operation and returns us to origin.
        """
        self.clear()

    def clear(self):
        """
        This clears the global variables and raises the target frame.
        """
        self.controller.show_frame(self.controller.target)
        self.controller.target = None
        self.controller.command = None


class ErrorWidget(Frame):
    """
    This presents a confirmation dialog sporting a confirm or cancel.
    """

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.rt_data = self.controller.rt_data
        self.temp = self.controller.temp
        self.error_message = self.temp['error_message'] = StringVar()
        self.last_target = self.temp['last_target'] = 'Writer'
        self.error_message.set('No Message loooooong test')
        self.base = Frame(
            self,
            bg=theme['main'],
            width=prx(30),
            height=pry(30)
        )
        self.base.grid(row=0, column=0)
        self.error_message_frame = Frame(
            self.base,
            width=prx(30),
            height=pry(15),
            # bg='red'
        )
        self.error_message_frame.grid(row=0, column=0)
        self.error_message_label = Label(
            self.error_message_frame,
            textvariable=self.error_message,
            width=prx(30),
            height=pry(15),
            image=get_spacer(),
            bg=theme['main'],
            fg=theme['buttontext'],
            compound=CENTER,
            font=(theme['font'], str(pointsy(3))),
            wraplength=pry(29)
        )
        self.error_message_label.pack()
        button_array(
            self.base,
            ['ok'],
            [
                self.ok_event
            ],
            1,
        )

    def ok_event(self):
        """
        This cancels the operation and returns us to origin.
        """
        self.clear()

    def clear(self):
        """
        This clears the global variables and raises the target frame.
        """
        print(self.controller.target)
        self.controller.show_frame(self.controller.target)
        self.controller.target = self.last_target
        print('setting new target', self.controller.target)
        self.controller.command = None


class QRCodeLabel(Label):
    """
    Cute little QR code maker.
    TODO: We need to stop this from cycling on startup
    """

    def __init__(self, parent, qr_data, scale=8):
        Label.__init__(self, parent)
        tmp_img = os.getcwd() + 'qr.png'
        url = pyqrcode.create(qr_data)
        url.png(tmp_img, scale=scale)
        tmr = image_resize(scr_y, scr_y, 'qr.png', 90, 90, folder_add='img/tmp/', raw=True)
        self.image = PhotoImage(file=tmr)
        self.x = self.image.width()
        self.y = self.image.height()
        self.configure(
            image=self.image
        )
        os.remove(tmp_img)


class QRCodeWidget(Frame):
    """
    This is the QR code frame we will use to onboard and bind downstream stages.
    """

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        global rt_data
        self.rt_data = controller.rt_data
        self.temp = self.rt_data['temp']
        self.qr_data = self.temp['qr_data']
        self.qr_label = None
        self.refresh = self.build_qr

    def build_qr(self):
        """
        This refreshes the QR code and displays the code in our widget.
        """
        if self.qr_label:
            self.clear()
        self.qr_label = QRCodeLabel(self, self.qr_data, theme['qrscale'])
        self.qr_label.pack()

    def drop_event(self):
        """
        This lifts the parent frame.
        """
        self.controller.show_frame(self.controller.target)

    def show(self):
        """
        Lift self.
        """
        self.tkraise()

    def clear(self):
        """
        This allows us to remove the qr data after we are finished with the code.
        """
        self.qr_label.destroy()


class LoadingIcon(Frame):
    """
    This is a cool animated loading icon.
    """

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller
        self.animated_label = LoadingAnimation(self)

        self.configure(
            width=prx(15),
            height=pry(15),
        )


class LoadingAnimation(Frame):
    """
    Nifty gif animmated widget.
    """

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.go = False
        self.total_frames = 51
        self.frames = list()
        for frame in range(self.total_frames):
            frame_file = 'Leonardo_' + f"{frame:05d}" + '.png'
            frame_file = img(frame_file, 15, 15, folder_add='Leonardo/')
            self.frames.append(PhotoImage(file=frame_file))
        self.label = Label(parent)
        self.label.configure(
            bg=theme['main']
        )
        self.label.pack()
        self.label.after(0, self.update, 0)

    # noinspection PyMethodOverriding
    def update(self, ind):
        """
        This is just an update loop.
        """
        if self.go:
            maxx = self.total_frames - 1
            frame = self.frames[ind]
            self.label.configure(image=frame)

            if ind >= maxx:
                ind = 0
            else:
                ind += 1
            self.after(maxx, self.update, ind)
        return self


class GifIcon(Frame):
    """
    This is a cool animated loading icon.
    """

    def __init__(self, parent, file, size=None):
        Frame.__init__(self, parent)
        if not size:
            size = (100, 100)
        self.go = False
        self.gif = GifAnimation(self, file, size=size)
        w, h = size
        self.configure(
            width=prx(w),
            height=pry(h),
        )


class GifAnimation(Frame):
    """
    Nifty gif animmated widget.

    Ref: https://github.com/python-pillow/Pillow/issues/3660
    """

    def __init__(self, parent, file, optimize=False, size=None):
        Frame.__init__(self, parent)
        if not size:
            size = (100, 100)
        # image = file
        image = img(file, *size)
        self.frames = list()
        self.go = False
        if optimize:
            self.total_frames = int(
                system_command(['identify', '-format', '"%n\\n"', image]).split('\n')[0].replace('"', ''))
            self.frames = [PhotoImage(file=image, format='gif -index %i' % i) for i in range(self.total_frames)]
        else:
            image = PilImage.open(image)
            self.framedesposal(image)
        self.label = Label(
            parent,
            bd=0,
            highlightthickness=0,
        )
        self.label.pack()
        self.label.after(0, self.update, 0)

    def appendtoframes(self, im):
        """
        Working on cleaning up the output.
        """
        im_copy = im.copy()
        im_copy.dispose_extent = im.dispose_extent
        im_copy.disposal_method = im.disposal_method
        im_copy.global_palette = im.global_palette
        self.frames.append(im_copy)

    def framedesposal(self, im):
        """
        Update frame disposals.
        """
        for i in range(1, im.n_frames):
            # Instead of combining the deltas into a single image as Pillow normally would
            # This clears the image data already loaded, giving us just the data from the new frame
            im.im = None
            im.dispose = None

            im.seek(i)

            self.appendtoframes(
                im
            )
        seq = list()
        for i in self.frames:
            seq.append(PilImageTk.PhotoImage(i))
        self.frames = seq

    # noinspection PyMethodOverriding
    def update(self, ind):
        """
        This is just an update loop.
        """
        # maxx = self.total_frames - 1
        maxx = len(self.frames) - 1
        frame = self.frames[ind]
        if self.go:
            self.label.configure(image=frame)

        if ind >= maxx:
            ind = 0
        else:
            ind += 1
        self.after(maxx, self.update, ind)
        return self


class SaveRemoteSettings:
    """
    This will save a new or updated setting to a downstream stage.
    """
    def __init__(self, controller):
        self.controller = controller
        self.command_event = self.controller.command_event
        print('sending new settings')
        self.controller.send(  # Transmit new settings.
            self.controller.stage_id,
            {
                'SENDER': self.controller.settings.director_id,
                'DATA': {'SETTINGS': self.controller.editvar}
            }
        )
        self.command_event('Calibrations', 'settings_save()')  # Inform the stage to update accordingly.


def stream_window(
        controller,
        parent,
        requested_data,
        requested_cycletime,
        terminator,
        target,
        varss,
        mode=None,
        command=None,
        no_border=False
):
    """
    This will create a simple frame listing titles on the left and values on the right.
    This data will be updated from a streamer thread in real time.
    """
    good = controller.check_for_stage(target)
    if good:
        streamer(controller, requested_data, requested_cycletime, terminator, target, varss, mode)  # Start stream
    while not controller.stream_ready:  # Wait for values
        time.sleep(0.1)
        pass
    base = Frame(
        parent,
        bg=theme['main'],
    )
    if not no_border:
        base.configure(
            highlightthickness=pry(1),
            highlightbackground=theme['entrybackground']
        )
    left = Frame(
        base,
        bg=theme['main'],
        padx=pry(1),
        pady=pry(1)
    )
    left.grid(row=0, column=0)
    right = Frame(
        base,
        bg=theme['main'],
        padx=pry(1),
        pady=pry(1)
    )
    right.grid(row=0, column=1)
    idx = 0
    for idx, var in enumerate(varss):  # Create rows of values.
        if 's_' in var:  # Exclude dummy labels.
            text = ''
        else:
            text = var
        just = LEFT
        an = 'w'
        if center:
            just = CENTER
            an = None
        lbll = config_text(
            Label(
                left,
                anchor=an,
                justify=just
            ),
            text=text
        )
        lbll.grid(row=idx, column=0, sticky=an)
        lblr = config_text(
            Label(
                right,
                anchor=an,
                justify=just
            ),
            text=varss[var]
        )
        lblr.grid(row=idx, column=1, sticky=an)

    exit_frame = Frame(
        base,
    )
    exit_frame.grid(row=idx + 1, columnspan=2)

    button_array(
        exit_frame,
        ['close'],
        [command],
    )

    return base


def streamer(controller, requested_data, requested_cycletime, terminator, target, varss, mode=None):
    """
    This will send a "send_stream" request to a target stage. then launch a thread to update a series of tkinter variables.
    NOTE this will use the send_command method within our controller.

    Example:
        requested_data = "IMU" - This will set up a stream sending the "IMU" key from the remote real time model
        requested_cycletime = 1 - Send the data once a second.
        terminator = <stream termination variable>
        target = Target frame to raise.
        varss = {
            'tiltcompensatedheading': tk.StringVar(),  - we pass a string var instance used elsewhere.
        }
        Note: the keys within the vars dictionary will be looked up as such: controller.rt_data['LISTENER'][<requested_data>][<key>].
    """
    def updater(ct, rd, rc, tm, tg, vrs):
        """
        This is our threaded realtime update loop.
        """
        fail = 0
        key = None
        if ct.stage_id:
            while not tm and fail < 10:
                tm = ct.stream_term
                # print(tm)
                try:
                    rds = rd.split("[")  # Split string of keys
                    key = '[' + rds[-1]  # Extract Last Key
                    dta = eval('ct.rt_data[\'LISTENER\'][ct.stage_id]' + key)
                    ct.stream_ready = True
                    # print('setting controller ready')
                    for vr in vrs:
                        var = vrs[vr]
                        try:
                            var.set(dta[vr])  # Update vars with new data.
                        except KeyError:  # Handle delays in transmission.
                            if isinstance(var, StringVar):
                                var.set('waiting')
                            elif isinstance(var, IntVar):
                                var.set(0)
                            elif isinstance(var, BooleanVar):
                                var.set(0.0)
                    time.sleep(rc)  # Wait for cycle time.
                    fail = 0
                except KeyError:
                    ct.stream_ready = False
                    fail += 1
                    print('waiting for data', '[' + ct.stage_id + ']' + key)
                    # print(ct.rt_data['LISTENER'])
                    time.sleep(1)
                    pass
        ct.stream_term = False
        ct.rt_data['temp']['datastream_term'] = False
        ct.command_event(tg, 'close_stream()')  # Close stream when we are finished.
        # print(ct.rt_data['LISTENER'])
        msg = ''
        if tm:
            msg = 'termination signal recieved'
        elif not fail < 10:
            msg = 'retry limit exceeded'
        print('requesting stream closure', msg)

    print('requesting stream')
    t = Thread(
        name=requested_data,
        target=updater,
        args=(
            controller,
            requested_data,
            requested_cycletime,
            terminator,
            target,
            varss
        )
    )
    t.start()
    requested_data = '"' + requested_data + '"'
    controller.command_event(target, 'send_stream(' + requested_data + ', ' + str(requested_cycletime) + ', "' + str(mode) + '")')


def center_weights(parent, row=True, rows=1, col=True, cols=1):
    """
    This centers the pparent's grid weights
    """
    if row:
        for rw in range(rows):
            parent.grid_rowconfigure(rw, weight=1)
    if col:
        for cl in range(cols):
            parent.grid_columnconfigure(cl, weight=1)


def list_stages(controller, parent):
    """
    This produces the list of stages that we have been paired with.
    """
    for button in controller.stage_buttons:
        try:
            button.destroy()
        except TclError:
            del button
    for stage_entry in controller.settings.stages:
        s_id = stage_entry
        stages = controller.rt_data['LISTENER']  # Get stages data model.
        if stage_entry in stages:
            if stages[stage_entry]['STATUS'] == 'confirmed':  # If connected, show in selector.
                s_name = controller.settings.stages[stage_entry]['name']
                try:  # Handle incomplete realtime model.
                    controller.stage_buttons.append(
                        config_stagelist_button(
                            Button(
                                parent.interior,
                                text=s_name,
                                command=lambda q=(s_id, s_name): select_stage(controller, *q)
                            ),
                            width=prx(20)
                        )
                    )
                    controller.stage_buttons[-1].pack()
                except KeyError as err:
                    print('stage list waiting for real time model', err)
            elif stage_entry == controller.stage_id:  # We need to check and remove the selected_stage here so we don't send network requests to a disconnected client.
                clear_selected_stage(controller)


def select_stage(controller, s_id, s_name):
    """
    This is the stage selection event.
    """
    controller.stagename.set('selected stage: ' + s_name)
    controller.stage_id = s_id
    controller.stagetarget = controller.stage_id
    controller.refresh()


def clear_selected_stage(controller, refresh=True):
    """
    This clears out a stage selection from the controller.
    """
    controller.stagename.set('')
    controller.stage_id = None
    controller.stage_target = None
    if refresh:
        controller.refresh()


def timed_element(parent, controller, element, timeout):
    """
    This presents a timed UX element that will distroy itself after the timeout has been reached.
    """
    def timed_thread_instance(pr, ct, el, tm):
        """
        This creates out element.
        """
        ele = el(pr, ct)
        _timeout = tm.get()
        while _timeout > 0:
            # print('timeout', _timeout)
            time.sleep(1)
            tm.set(
                tm.get() - 1
            )
            _timeout = tm.get()
        ele.destroy()

    th = Thread(target=timed_thread_instance, args=(parent, controller, element, timeout,))
    th.start()


def chkvar_handler(chkvar):
    """
    This emulates checkbox toggle behavior within a button.
    """
    state = chkvar.get()
    nstate = 1
    if state:
        nstate = 0
    if isinstance(chkvar, StringVar):
        nstate = str(nstate)
    elif isinstance(chkvar, IntVar):
        nstate = int(nstate)
    else:
        pass
    chkvar.set(nstate)


def config_checkbox(parent, text, intvar, command=None):
    """
    This creates a checkbox.
    """
    chk = Checkbutton(
        parent,
        command=command,
        width=prx(0.25),
        height=pry(2),
        bg=theme['main'],
        fg='black',
        highlightcolor=theme['main'],
        highlightthickness=0,
        activeforeground=theme['main'],
        text=text,
        variable=intvar,
        image=get_spacer(),
        relief=FLAT,
        bd=0
    )
    chk.pack(side=LEFT)
    return chk


# def button_array(parent, tils, coms, rw=0, col=0, vert=False):
#     """
#     Creates a horizontal or vertical series of buttons.
#     """
#     # bgm = PhotoImage(file=img('fullbuttonframe.png', 10, 10))
#     for idx, (title, command) in enumerate(zip(tils, coms)):
#         t_frame = Frame(
#             parent,
#             bg=theme['main'],
#             width=prx(20),
#             height=pry(10),
#         )
#         if not vert:
#             t_frame.grid(row=rw, column=idx)
#         else:
#             t_frame.grid(row=idx, column=col)
#         config_single_button(
#             t_frame,
#             title,
#             command
#         )


def button_array(parent, tils, coms, rw=0, col=0, vert=False, size=(10, 10), aspect=True, label=False):
    """
    Creates a horizontal or vertical series of buttons.
    """
    x, y = size
    for idx, (title, command) in enumerate(zip(tils, coms)):
        t_frame = Frame(
            parent,
            # bg=theme['main'],
            width=prx(x),
            height=pry(y),
        )
        if not vert:
            t_frame.grid(row=rw, column=idx + col)
        else:
            t_frame.grid(row=idx + rw, column=col)
        config_single_button(
            t_frame,
            title,
            command,
            size,
            aspect,
            label
        )


def config_single_button(parent, text, command, size=None, aspect=True, label=False):
    """
    This creates a single button.

    NOTE: We can now use this to create labels in the same manor.
    """
    if not size:
        size = (10, 10)
    x, y = size

    if label:
        btn = config_text(
            Label(
                parent,
                width=prx(x),
                height=pry(y),
            ),
            size=x,
            pad=y
        )
    else:
        file = img('fullbuttonframe.png', *size, aspect=aspect)
        bgm = PhotoImage(file=file)
        btn = config_button(
            Button(
                parent,
                command=command,
                width=prx(x),
                height=pry(y),
                image=bgm
            )
        )
        btn.image = bgm
    if isinstance(text, StringVar) or isinstance(text, IntVar):
        btn.configure(textvariable=text)
    else:
        btn.configure(text=text)
    btn.pack()
    return btn


def config_button(element, size=2):
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
        compound='center',
        font=(theme['font'], pointsy(size))
    )
    return element


def config_number_button(element):
    """
    This styles the buttons on the number pad.
    """
    el = config_button(element)
    el.configure(
        font=(theme['font'], str(pointsy(5))),
    )


def config_word_button(element):
    """
    This styles the buttons on the keyboard.
    """
    el = config_button(element)
    el.configure(
        font=(theme['font'], str(pointsy(5))),
    )


def config_file_button(element, bad=False):
    """
        This styles the buttons on the file browser.
        """
    el = config_button(element)
    el.configure(
        font=(theme['font'], str(pointsy(5))),
        anchor=W,
        width=20,
        pady=pry(2),
        justify=LEFT
    )
    if bad:
        el.configure(
            fg=theme['badfiletext']
        )
    return element


def config_stagelist_button(element, bad=False, width=10):
    """
        This styles the buttons on the file browser.
        """
    im = get_spacer()
    el = config_button(element)
    el.configure(
        font=(theme['font'], str(pointsy(5))),
        anchor=W,
        width=width,
        pady=pry(2),
        justify=LEFT,
        image=im
    )
    el.image = im
    if bad:
        el.configure(
            fg=theme['badfiletext']
        )
    return element


def config_rehearsallist_button(element, bad=False):
    """
        This styles the buttons on the rehearsal list.
        """
    spacer = get_spacer()
    el = config_button(element)
    el.configure(
        font=(theme['font'], str(pointsy(5))),
        anchor=W,
        width=prx(45),
        pady=pry(2),
        justify=LEFT,
        image=spacer,
    )
    el.image = spacer
    if bad:
        el.configure(
            fg=theme['badfiletext']
        )
    return element


def config_editor_button(element, text, bad=False, size=3, width=20):
    """
        This styles the buttons on the rehearsal list.
        """
    spacer = get_spacer()
    el = config_button(element)
    el.configure(
        font=(theme['font'], str(pointsy(size))),
        anchor=W,
        width=prx(width),
        pady=pry(2),
        justify=LEFT,
        image=spacer,
    )
    el.image = spacer
    if bad:
        el.configure(
            fg=theme['badfiletext']
        )
    if isinstance(text, StringVar):
        el.configure(
            textvariable=text
        )
    else:
        el.configure(
            text=text
        )
    return element


def config_text(element, text=None, size=2, pad=2):
    """
    This takes an element and configures the text properties
    """
    if not text:
        text = str()
    element.configure(
        font=(theme['font'], pointsy(size)),
        pady=pry(pad),
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


def safe_raise(controller, fraise, fsource, chain=None):
    """
    This safly rases widgets so they don't stack.
    TODO: we may need to set the last_frame flag here in the future.

    :param controller: Passed instance of the master controller.
    :param fraise: The name of the frame to raise.
    :param fsource: THe name of the frame to fall back on.
    :param chain: Optional list of frames to rais in order for more complex situations.
    :type chain: NoneType, list
    """
    if controller:
        if chain:
            for f in chain:
                controller.show_frame(f)
        controller.show_frame(fsource)
        controller.show_frame(fraise)
    else:
        if chain:
            for f in chain:
                f.tkraise()
        fsource.tkraise()
        fraise.tkraise()


def safe_drop(controller, chain):
    """
    This raises a chain of frames so we can properly drop frames from the background.
    """
    for f in chain:
        if controller:
            controller.show_frame(f)
        else:
            f.tkraise()


def open_window(parent):
    """
    This opens a new window.
    """
    return Toplevel(parent)


def cp(to_move, to_correct):
    """
    This offsets the position of an object from the the side to the middle.

    Note: This uses percentages.
    """
    return to_move - (to_correct / 2)


def cparent(parent, child, border=True):
    """
    This will take the size of the parent widget, compare against the size of the child widget and then
    center the child with respect to the parent.
    """

    parent.update()
    p_w = parent.winfo_reqwidth()
    p_h = parent.winfo_reqheight()
    child.place(  # Place child out of signt until we can get the size.
        x=999999,
        y=999999
    )
    if border:
        child.configure(
            highlightthickness=pry(1),
            highlightbackground=theme['entrybackground'],
        )
    child.update()
    c_w = child.winfo_reqwidth()
    c_h = child.winfo_reqheight()
    x = center(p_w, c_w)
    y = center(p_h, c_h)
    child.place(  # Center child.
        x=x,
        y=y
    )
    return child


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


def img(image, x_percent, y_percent, aspect=True, folder_add=False):
    """
    Quick and dirty way to grab images.

    :type image: str
    :type x_percent: int
    :type y_percent: int
    :type aspect: bool
    :type folder_add: bool, str
    """
    if not folder_add:
        image = file_rename(settings.theme + '_', image, reverse=True)
    image = image_resize(
        scr_x,
        scr_y,
        image,
        x_percent,
        y_percent,
        aspect,
        folder_add
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

# if __name__ == '__main__':
app.mainloop()
