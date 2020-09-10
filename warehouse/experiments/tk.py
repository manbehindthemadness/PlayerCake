"""
Tkinter playground...

Count frames: identify -format "%n\n" Hover.gif | head -n 1

'/home/pi/playercake/img/base/Hover.gif'
"""
import os
from tkinter import *

from warehouse.system import system_command

os.environ['DISPLAY'] = 'localhost:11.0'
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])
display = system_command(['echo', '$DISPLAY'])

root = Tk()


class Animation(Frame):
    """
    Nifty gif animmated widget.
    """
    def __init__(self, parent):
        Frame.__init__(self, parent)
        image = '/home/pi/playercake/img/base/Hover.gif'
        self.total_frames = int(system_command(['identify', '-format', '"%n\\n"', image]).split('\n')[0].replace('"', ''))
        self.frames = [PhotoImage(file=image, format='gif -index %i' % i) for i in range(self.total_frames)]
        self.label = Label(parent)
        self.label.pack()
        self.label.after(0, self.update, 0)

    # noinspection PyMethodOverriding
    def update(self, ind):
        """
        This is just an update loop.
        """
        maxx = self.total_frames - 1
        frame = self.frames[ind]

        self.label.configure(image=frame)

        if ind >= maxx:
            ind = 0
        else:
            ind += 1
        self.after(maxx, self.update, ind)
        return self


label = Animation(root)
root.mainloop()
