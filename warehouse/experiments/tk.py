import tkinter as tk
from tkinter import *
import os
from warehouse.system import system_command

os.environ['DISPLAY'] = 'localhost:11.0'
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])


def main():
    root = tk.Tk()
    numpad = NumPad(root, StringVar())
    root.mainloop()


class NumPad(Frame):
    """
    Creates a simple number pad.
    """
    def __init__(self, root, model):
        Frame.__init__(self, root)
        self.model = model
        self.grid()
        self.numvar = StringVar()
        self.number = None
        self.numpad_create()
        self.b = None

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
        self.model.set(int(self.number))
        # TODO: we need to drop the numpad here.

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
        c = 1
        Label(self, textvariable=self.numvar, width=15).grid(row=0, columnspan=3)
        for b in btn_list:
            self.b = Button(self, text=b, width=5, command=lambda b=b: self.set_num(b)).grid(row=r, column=c)
            c += 1
            if c > 3:
                c = 1
                r += 1
        Button(self, text='del', width=5, command=lambda: self.delete_nums()).grid(row=4, column=2)
        Button(self, text='go', width=5, command=lambda: self.pass_nums()).grid(row=4, column=3)


main()
