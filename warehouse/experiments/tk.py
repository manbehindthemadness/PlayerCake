"""
Tkinter playground...

Count frames: identify -format "%n\n" Hover.gif | head -n 1

'/home/pi/playercake/img/base/Hover.gif'
"""
import tkinter
import queue
import os
from warehouse.system import system_command


os.environ['DISPLAY'] = 'localhost:11.0'
os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
system_command(['/usr/bin/xhost', '+'])
system_command(['echo', '$DISPLAY'])


class Flash(tkinter.Toplevel):
    def __init__(self, root, **options):
        tkinter.Toplevel.__init__(self, root, width=100, height=20, **options)

        self.overrideredirect(True) # remove header from toplevel
        self.root = root

        self.attributes("-alpha", 0.0) # set transparency to 100%

        self.queue = queue.Queue()
        self.update_me()

    def write(self, message):
        self.queue.put(message) # insert message into the queue

    def update_me(self):
        #This makes our tkinter widget threadsafe
        # http://effbot.org/zone/tkinter-threads.htm
        try:
            while 1:
                message = self.queue.get_nowait() # get message from the queue

                # if a message is received code will execute from here otherwise exception
                # http://stackoverflow.com/questions/11156766/placing-child-window-relative-to-parent-in-tkinter-pythons
                x = root.winfo_rootx() # set x coordinate of root
                y = root.winfo_rooty() # set y coordinate of root
                width = root.winfo_width() # get the width of root
                self.geometry("+%d+%d" % (x+width-self.winfo_width() ,y)) # place in the top right cornder of root

                self.fade_in()  # fade in when a message is received
                label_flash = tkinter.Label(self, text=message, bg='black', fg='white', padx=5, pady=5)
                label_flash.pack(anchor='e')
                self.lift(self.root)

                def callback():
                    label_flash.after(2000, label_flash.destroy) # destroy the label after 5 seconds
                    self.fade_away() # fade away after 3 seconds
                label_flash.after(3000, callback)

        except queue.Empty:
            pass
        self.after(100, self.update_me) # check queue every 100th of a second

    # http://stackoverflow.com/questions/3399882/having-trouble-with-tkinter-transparency
    def fade_in(self):
        alpha = self.attributes("-alpha")
        alpha = min(alpha + .01, 1.0)
        self.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.after(10, self.fade_in)

    # http://stackoverflow.com/questions/22491488/how-to-create-a-fade-out-effect-in-tkinter-my-code-crashes
    def fade_away(self):
        alpha = self.attributes("-alpha")
        if alpha > 0:
            alpha -= .1
            self.attributes("-alpha", alpha)
            self.after(10, self.fade_away)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.minsize(700, 300)
    root.geometry("700x500")

    flash = Flash(root) # create toplevel instance

    def callback():
        # put a delay between each message so we can check the behaviour depending on the lenght of the delay between messages
        import time
        flash.write('Hello World')
        time.sleep(1)
        flash.write('Ready!')
        time.sleep(2)
        flash.write('Steady!')
        time.sleep(4)
        flash.write('Go!')

    # create a thread to prevent the delays from blocking our GUI
    import threading
    t = threading.Thread(target=callback)
    t.daemon = True
    t.start()
    root.mainloop()
    exit()