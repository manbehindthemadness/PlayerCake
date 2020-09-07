"""
Tkinter playground...
"""

import os
from tkinter import *

from warehouse.system import system_command

os.environ['DISPLAY'] = 'localhost:11.0'
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])


class VerticalScrolledFrame(Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent):
        Frame.__init__(self, parent)

        # create a canvas object and a vertical scrollbar for scrolling it

        canvas = Canvas(self, bd=0, highlightthickness=0, bg='white')
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.canvasheight = 2000

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas, height=self.canvasheight)
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


if __name__ == "__main__":

    class SampleApp(Tk):
        """
        sample
        """
        def __init__(self, *args, **kwargs):
            root = Tk.__init__(self, *args, **kwargs)

            self.frame = VerticalScrolledFrame(root)
            self.frame.pack()
            # self.label = Label(text="Shrink the window to activate the scrollbar.")
            # self.label.pack()
            self.buttons = list()
            self.ext = '.obj'
            self.dir = self.plot_dir = '/home/pi/playercake/plots/'
            self.list_dirs()

        def list_dirs(self):
            """
            This will list the files and folder under the self.dir path.
            """
            self.buttons.append(Button(self.frame.interior, text='...', command=lambda: self.up_event()))
            self.buttons[-1].pack()
            for i in os.listdir(self.dir):
                if os.path.isdir(self.dir + i):
                    self.buttons.append(Button(self.frame.interior, text=i, command=lambda q=i: self.folder_event(q)))
                else:
                    if i[-4:] == self.ext:
                        self.buttons.append(Button(self.frame.interior, text=i))
                    else:
                        self.buttons.append(Label(self.frame.interior, text=i))
                self.buttons[-1].pack()

        def clear_list(self):
            """
            This clears the contents of the scroll window
            """
            for button in self.buttons:
                button.destroy()

        def folder_event(self, folder):
            """
            This will drop us into a folder on selection.
            """
            self.dir += folder + '/'
            print(self.dir)
            self.clear_list()
            self.list_dirs()

        def up_event(self):
            """
            This will take us up one folder level.
            """
            self.dir = '/' + self.dir.split('/', 1)[-1].rsplit('/', 2)[0] + '/'
            print(self.dir)
            self.clear_list()
            self.list_dirs()

    app = SampleApp()
    app.mainloop()
