"""
This is our top-level ux file

This is the main program loop for the user interface.

Tips for messed up X: https://www.ibm.com/support/pages/x11-forwarding-ssh-connection-rejected-because-wrong-authentication
NOTE: Copy the .Xauthority file from root to pi.

NOTE: THE X-SERVER MUST BE RUNNING!

Good REf: https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter

TODO: NOTE!! Buttons and Labels are sized by the number of chars UNLESS they have an image!

TODO: We seriously need to break these inits down into classes...
"""
import os
import tkinter as tk
import uuid
from tkinter import *
from tkinter.filedialog import askopenfilename

import pyqrcode
from PIL import Image as PilImage, ImageTk as PilImageTk

# import settings
from settings import settings
from warehouse.system import system_command
from warehouse.utils import percent_of, percent_in, file_rename, image_resize
from writer.plot import pymesh_stl


scr_x, scr_y = settings.screensize

theme = settings.themes[settings.theme]
# defaults = settings.defaults

# This crap is for tunneling the app over ssh
os.environ['DISPLAY'] = settings.display
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])
system_command(['echo', '$DISPLAY'])

rt_data = dict()


def get_spacer():
    """
    Returns a spacer image.
    """
    return PhotoImage(file='img/base/spacer.png')


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
            ['sudo', 'service', 'playercake', 'restart']
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
        # self.defaults = defaults
        # for sett in self.defaults:  # Populate defaults
        #     self.rt_data[sett] = StringVar()
        #     self.rt_data[sett].set(str(defaults[sett]))
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
        self.render_button = self.full_button(
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
            text='rehersal'
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
            command='',
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
            text='pair'
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
            height=self.panel_size / 5,
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
        This will raise the audition frame.
        """
        self.controller.refresh('Rehearsal')
        safe_raise(self.controller, 'Rehearsal', 'Writer')
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
        self.stage_id = str()
        self.stage_buttons = list()
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
            width=494,
            height=pry(75),
            x=cp(prx(35), 494),
            y=cp(pry(45), pry(75))
        )
        self.class_label = GifIcon(
            self.classes,
            self.locate_image('animal-gaits.gif')
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
            0,
            0
        )
        button_array(
            self.class_selection_frame,
            ['trot', 'canter', 'gallup'],
            [
                lambda: self.select_class('trot'),
                lambda: self.select_class('canter'),
                lambda: self.select_class('gallup')
            ],
            1,
            0
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
            width=360,
            height=pry(45),
            x=cp(prx(35), 360),
            y=cp(pry(45), pry(50))
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
            self.locate_image('rotate.gif')
        )
        self.rotate_label.grid(row=0, column=0)
        self.sidestep_label = GifIcon(
            self.scaler_icon_frame,
            self.locate_image('sidestep.gif')
        )
        self.sidestep_label.grid(row=0, column=1)
        button_array(
            self.scaler_icon_frame,
            ['rotate', 'sidestep'],
            [
                lambda: self.select_scaler('rotate'),
                lambda: self.select_scaler('sidestep')
            ],
            1,
            0
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
            2,
            0
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
            0,
            0
        )

        #  ##############
        #  configure base
        #  ##############
        self.base = Frame(
            self,
            bg=theme['main'],
            width=prx(70),
            height=pry(90)
        )
        self.base.place(  # Place Base.
            width=prx(70),
            height=pry(90)
        )
        #  ##########
        #  Left panel
        #  ##########
        self.stage_title_frame = Frame(  # Place title.
            self.base,
            width=prx(23),
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
            width=prx(25),
            height=pry(70),
        )
        self.stage_selector.grid(row=1, column=0, sticky=N)
        self.stage_list = VerticalScrolledFrame(self.stage_selector)
        self.stage_list.pack()
        self.selected_stage_frame = Frame(
            self.base,
            width=prx(23),
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
            0,
            0
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
                '',
                lambda: self.scaler_selector()
            ],
            0,
            1,
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
            2,
            0
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
        for stage_entry in settings.stages:
            s_id = stage_entry
            s_name = settings.stages[stage_entry]['name']
            self.stage_buttons.append(
                 config_stagelist_button(
                     Button(
                         self.stage_list.interior,
                         text=s_name,
                         command=lambda q=(s_id, s_name): self.select_stage(*q)
                     )
                 )
            )
            self.stage_buttons[-1].pack()

    def select_stage(self, s_id, s_name):
        """
        This is the stage selection event.
        """
        self.stagename.set('selected stage: ' + s_name)
        self.stage_id = s_id
        self.stagetarget = self.stage_id
        self.refresh()

    def class_selector(self):
        """
        Raises the class selector frame and starts the animation.
        """
        self.class_label.gif.go = True
        safe_raise(False, self.classes, self.base)

    def select_class(self, c_name):
        """
        This sets the script class variable and raises self.
        Stops the animation.
        """
        self.script_class.set(c_name)
        self.refresh()
        self.base.tkraise()
        self.class_label.gif.go = False

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
        self.script_scaler.set(s_name)
        self.refresh()
        self.base.tkraise()
        self.rotate_label.gif.go = False
        self.sidestep_label.gif.go = False

    def list_rehearsals(self):
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
                        command=lambda q=(rh, rdata): self.open_rehearsal(*q),
                    )
                )
            )
            self.rehearsal_buttons[-1].pack()
            safe_raise(False, self.open_frame, self.base)

    def open_rehearsal(self, rname, rdata):
        """
        This will open one of our saved rehearsals.
        """
        self.rehearsalname.set(rname)
        self.rehearsaldata = rdata
        self.cancel_rehearsal()
        self.controller.target = ['Writer', 'Rehearsal', 'CloseWidget']

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
        self.list_stages()
        self.controller.target = 'Writer'

    @staticmethod
    def locate_image(image):
        """
        This lets us pull images without post processing.
        """
        return 'img/base/' + file_rename(settings.theme + '_', image, reverse=True)


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
        self.defaults = settings.defaults
        for sett in self.defaults:  # Populate defaults
            self.rt_data[sett] = StringVar()
            self.rt_data[sett].set(str(self.defaults[sett]))
        self.target = self.temp['targetframe'] = 'Writer'  # This is the page we will raise after a widget is closed.
        self.entertext = self.temp['entertext'] = 'enter'
        self.stagedata = self.temp['stagedata'] = dict()
        self.stagetarget = self.temp['stagetarget'] = str()
        self.rehersals = rt_data['rehearsals'] = settings.rehearsals
        self.num_max = 100  # Maximum default number for the num pad.
        self.scripts = rt_data['scripts'] = settings.scripts
        self.has_plot = False
        self.command = None
        self.rt_data['key_test'] = StringVar()  # TODO: This is just for testing the keyboard.
        self.rt_data['key_test'].set('')
        self.update()  # I wish I had thought of this sooner...

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
        for F in (  # Ensure the primary classes are passed before the widgets.
            Home,
            Writer,
            Audience,
            Rehearsal,
            Keyboard,
            NumPad,
            FileBrowser,
            CloseWidget,
            QRCodeWidget,
            LoadingIcon,
            ConfirmationWidget,
            ErrorWidget
        ):
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
                    height=pry(92),
                    width=prx(71),
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

        # home.show()
        self.show_frame('Home')

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
        self.go = Button(self, text='go', width=width, height=height, command=lambda: self.pass_nums())
        config_number_button(self.go)
        self.go.grid(row=4, column=2)


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
        self.controller.show_frame(self.controller.target)
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
            canvas.yview_moveto(self.scrollposition / self.canvasheight)

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
            canvas.yview_moveto(self.scrollposition / self.canvasheight)

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
            0
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
            0
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
        self.controller.show_frame(self.controller.target)
        self.controller.target = None
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
    def __init__(self, parent, file):
        Frame.__init__(self, parent)
        self.go = False
        self.gif = GifAnimation(self, file)
        self.configure(
            width=prx(15),
            height=pry(15),
        )


class GifAnimation(Frame):
    """
    Nifty gif animmated widget.

    Ref: https://github.com/python-pillow/Pillow/issues/3660
    """

    def __init__(self, parent, file, optimize=False):
        Frame.__init__(self, parent)
        image = file
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
            highlightthickness=0
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


def button_array(parent, tils, coms, rw, col, vert=False):
    """
    Creates a horizontal or vertical series of buttons.
    """
    bgm = PhotoImage(file=img('fullbuttonframe.png', 10, 10))
    for idx, (title, command) in enumerate(zip(tils, coms)):
        t_frame = Frame(
            parent,
            bg=theme['main'],
            width=prx(20),
            height=pry(10),
        )
        if not vert:
            t_frame.grid(row=rw, column=idx)
        else:
            t_frame.grid(row=idx, column=col)
        t_button = config_button(
            Button(
                t_frame,
                command=command,
                width=prx(10),
                height=pry(10),
                image=bgm
            )
        )
        t_button.image = bgm
        if isinstance(title, StringVar):
            t_button.configure(textvariable=title)
        else:
            t_button.configure(text=title)
        t_button.pack()


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


def config_stagelist_button(element, bad=False):
    """
        This styles the buttons on the file browser.
        """
    el = config_button(element)
    el.configure(
        font=(theme['font'], str(pointsy(5))),
        anchor=W,
        width=10,
        pady=pry(2),
        justify=LEFT
    )
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


def safe_raise(controller, fraise, fsource, chain=None):
    """
    This safly rases widgets so they don't stack.

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

app.mainloop()
