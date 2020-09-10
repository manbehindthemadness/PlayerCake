"""
Tkinter playground...

Count frames: identify -format "%n\n" Hover.gif | head -n 1

'/home/pi/playercake/img/base/Hover.gif'
"""
import os
from tkinter import *
from PIL import Image, ImageTk
from warehouse.utils import image_resize
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
        image = '/home/pi/playercake/img/base/Leonardo/'
        self.total_frames = 51
        self.frames = list()
        for frame in range(self.total_frames):
            frame_file = 'Leonardo_' + f"{frame:05d}" + '.png'
            self.frames.append(PhotoImage(file=image + frame_file))
        # self.total_frames = int(system_command(['identify', '-format', '"%n\\n"', image]).split('\n')[0].replace('"', ''))
        # self.frames = [PhotoImage(file=image, format='gif -index %i' % i) for i in range(self.total_frames)]
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

# root = Tk()
#
#
# class Animation(Frame):
#     """
#     Nifty gif animmated widget.
#     """
#     def __init__(self, parent):
#         Frame.__init__(self, parent)
#         image = '/home/pi/playercake/img/base/Hover.gif'
#         self.total_frames = int(system_command(['identify', '-format', '"%n\\n"', image]).split('\n')[0].replace('"', ''))
#         self.frames = [PhotoImage(file=image, format='gif -index %i' % i) for i in range(self.total_frames)]
#         self.label = Label(parent)
#         self.label.pack()
#         self.label.after(0, self.update, 0)
#
#     # noinspection PyMethodOverriding
#     def update(self, ind):
#         """
#         This is just an update loop.
#         """
#         maxx = self.total_frames - 1
#         frame = self.frames[ind]
#
#         self.label.configure(image=frame)
#
#         if ind >= maxx:
#             ind = 0
#         else:
#             ind += 1
#         self.after(maxx, self.update, ind)
#         return self
#
#
# label = Animation(root)
# root.mainloop()


# class MyLabel(Label):
#     def __init__(self, master, filename):
#         im = Image.open(filename)
#         seq = []
#         try:
#             while 1:
#                 seq.append(im.copy())
#                 im.seek(len(seq)) # skip to next frame
#         except EOFError:
#             pass # we're done
#
#         try:
#             self.delay = im.info['duration']
#         except KeyError:
#             self.delay = 100
#
#         first = seq[0].convert('RGBA')
#         self.frames = [ImageTk.PhotoImage(first)]
#
#         Label.__init__(self, master, image=self.frames[0])
#
#         temp = seq[0]
#         for image in seq[1:]:
#             temp.paste(image)
#             frame = temp.convert('RGBA')
#             self.frames.append(ImageTk.PhotoImage(frame))
#
#         self.idx = 0
#
#         self.cancel = self.after(self.delay, self.play)
#
#     def play(self):
#         self.config(image=self.frames[self.idx])
#         self.idx += 1
#         if self.idx == len(self.frames):
#             self.idx = 0
#         self.cancel = self.after(self.delay, self.play)
#
#
# root = Tk()
# anim = MyLabel(root, '/home/pi/playercake/img/base/Hover.gif')
# anim.pack()
#
# def stop_it():
#     anim.after_cancel(anim.cancel)
#
# Button(root, text='stop', command=stop_it).pack()
#
# root.mainloop()