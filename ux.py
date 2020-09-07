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
# rt_data['temp'] = dict()


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
        self.folder = None
        self.ext = None
        # self.rt_data['temp'] = dict()
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

        self.controller = controller
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
            command='',
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
            command='',
            text='receive'
        )
        self.receive_button.grid(row=6, columnspan=2)
        self.pair_button = self.full_button(
            self.left_panel_frame,
            'fullbuttonframe.png',
            command=lambda: self.show_keyboard('key_test'),
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
        self.ext = self.temp['ext'] = '.obj'
        self.folder = self.temp['folder'] = settings.plot_dir  # Get working directory.
        self.show_file_browser('folder')
        # self.rt_data['plotfile'] = openfile('/plots')
        # self.plotfile.set(
        #     self.rt_data['plotfile'].split('/')[-1]
        # )

    def render_plotfile(self):
        """
        This will render the actual plots into the writer app.
        """
        if self.plot:  # Clear if needed.
            self.plot.get_tk_widget().pack_forget()  # Clear old plot.

        self.update_defaults()  # update with latest config.

        plotfile = self.rt_data['plotfile'] = self.temp['targetfile'].get()  # Fetch plot file.
        if plotfile:
            if self.plot:  # Clear if needed.
                self.plot.get_tk_widget().pack_forget()  # Clear old plot.
            self.plot = self.plotter(plotfile, self.plot_frame, theme, settings.defaults, 1, self.rt_data)  # TODO: This will need to be revised for simulations.
            self.plot.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH)  # Fetch canvas widget.
        return self.plot

    # def get_word(self):

    def show_numpad(self, varname):
        """
        Lifts the numberpad page.

        TODO: We need to figure out some sore of clamp so we can prevent impossible numbers from being entered.

        :param varname: String var to set.
        :type varname: str
        """
        # print(varname, self.rt_data[varname].get())
        self.temp['number'].set(varname)
        self.controller.show_frame("NumPad")

    def show_keyboard(self, varname):
        """
        Lifts the keyboard page.
        """
        print('showing keyboard')
        self.temp['word'].set(varname)
        self.controller.show_frame("Keyboard")

    def show_file_browser(self, varname):
        """
        Lifts the file browser page.
        """
        self.temp[varname] = settings.plot_dir
        self.controller.clear('FileBrowser')
        self.controller.show_frame('FileBrowser')


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
        self.rt_data['temp'] = dict()
        self.rt_data['key_test'] = StringVar()  # TODO: This is just for testing the keyboard.
        self.rt_data['key_test'].set('')

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
        for F in (Home, Writer, Audience, Keyboard, NumPad, FileBrowser,):  # Ensure the primary classes are passed before the widgets.
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
        frame = self.get_frame(page_name)
        frame.tkraise()

    def clear(self, page_name):
        """
        This triggers a page to clear or refresh contents.
        """
        frame = self.get_frame(page_name)
        frame.clear()


class NumPad(Frame):
    """
    Creates a simple number pad.
    """
    def __init__(self, parent, controller, target='Writer'):
        Frame.__init__(self, parent)
        global rt_data
        self.rt_data = rt_data
        self.target = target
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
            self.get_num().set(self.numvar.get())
            self.temp['number'].set('0')
        self.controller.show_frame(self.target)
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

    def __init__(self, parent, controller, target='Writer'):
        Frame.__init__(self, parent)
        global rt_data
        self.rt_data = rt_data
        self.temp = self.rt_data['temp']
        self.target = target
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
                        ('a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", "enter"),
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
                        # flat, groove, raised, ridge, solid, or sunken
                        # store_button['relief'] = "sunken"
                        # store_button['bg'] = "powderblue"
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
            self.word = ''
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

    def set_word(self,  word):
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
        self.controller.show_frame(self.target)
        self.wordvar.set('')
        self.word = ''


class FileBrowser(Frame):
    """
    This is a pretty cute touch oriented file browser.
    """
    def __init__(self, parent, controller, target='Writer'):
        Frame.__init__(self, parent)
        global rt_data
        self.rt_data = rt_data
        self.temp = rt_data['temp']
        self.controller = controller
        self.frame = VerticalScrolledFrame(self)  # Change this to get the lifting right.
        self.frame.pack()
        self.target = target
        self.buttons = list()
        self.ext = self.temp['ext']
        self.dir = self.temp['folder']
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
        self.buttons[-1].pack()
        for i in os.listdir(self.dir):
            if os.path.isdir(self.dir + i):
                self.buttons.append(
                    config_file_button(Button(self.frame.interior, text=i + '/', command=lambda q=i: self.folder_event(q)))
                )
            else:
                if i[-4:] == self.ext:
                    self.buttons.append(
                        config_file_button(Button(self.frame.interior, text=i, command=lambda q=i: self.select_event(q)))
                    )
                else:
                    self.buttons.append(
                        config_file_button(Label(self.frame.interior, text=i), True)
                    )
            self.buttons[-1].pack()

    def clear(self):
        """
        This clears the contents of the scroll window
        """
        for button in self.buttons:
            button.destroy()
            del button

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
        """
        self.temp['targetfile'].set(self.temp['folder'] + '/' + filename)  # Build full path.
        self.controller.show_frame(self.target)  # Set global target file.


class VerticalScrolledFrame(Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent):
        Frame.__init__(self, parent)

        # create a canvas object and a vertical scrollbar for scrolling it

        canvas = Canvas(
            self,
            bg=theme['main'],
            height=pry(70)

        )
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.canvasheight = pry(70)
        self.canvaswidth = pry(40)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas, height=self.canvasheight, width=self.canvaswidth)
        self.interior.configure(
            bg=theme['main'],
        )
        self.interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            self.event = event
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            self.event = event
            if interior.winfo_reqwidth() != canvas.winfo_width():
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

            sectionmoved = 15
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

    def clear(self):
        """
        This clears the interior.
        """
        self.interior.pack_forget()


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
