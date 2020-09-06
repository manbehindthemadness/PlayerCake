import os
from tkinter import *

from warehouse.system import system_command

os.environ['DISPLAY'] = 'localhost:11.0'
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])


class Keyboard(Frame):
    """
    Virtual Keyboard.

    TODO: Insure to create parent, controller and default text passage in the INIT statement.
    """

    def __init__(self, *args, **kwargs):
        Frame.__init__(self, *args, **kwargs)
        self.stringvars = list()
        self.keys_lower = list()
        self.input = StringVar()
        self.text = str()
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
            store_section = Frame(self)
            store_section.pack(side='left', expand='yes', fill='both', padx=10, pady=10, ipadx=10, ipady=10)
            input_frame = Frame(store_section)  # Create input label.
            input_frame.pack(side='top', expand='yes', fill='both')
            input_label = Label(input_frame, textvariable=self.input)
            input_label.pack(side='top', expand='yes', fill='both')
            for layer_name, layer_properties, layer_keys in key_section:
                store_layer = LabelFrame(store_section)
                store_layer.pack(layer_properties)
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
                        store_button['relief'] = "sunken"
                        store_button['bg'] = "powderblue"
                        store_button['command'] = lambda q=txt: self.button_command(q)
                        store_button.pack(side='left', fill='both', expand='yes')
        return

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
            self.text = self.text[0:-1]
        elif ename == 'space':
            self.text += ' '
        elif ename == 'enter':
            print('enter command!', self.text)
            self.text = ''
            # TODO: Pass variables here!
            # TODO: Drop keyboard frame here!
        else:
            self.text += event.get()
        self.input.set(self.text)
        return event


# Creating Main Window
def main():
    """
    mainloop.
    """
    root = Tk(className=" Python Virtual KeyBoard")
    Keyboard(root).pack()
    root.mainloop()
    return


# Function Trigger
main()
