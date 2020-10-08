"""
This is where we will keep our thread saftey workaround.

https://serverfault.com/questions/433240/how-to-set-up-memcached-to-use-unix-socket/521021
https://guides.wp-bullet.com/configure-memcached-to-use-unix-socket-speed-boost/
"""
from threading import Thread as T
import memcache
import time
import random

mc = memcache.Client(['unix:/var/run/memcached/memcached.sock'])  # Connect to cache socket.

mc.flush_all()  # Clear cache at runtime.


class Thread:
    """
    This does it's best to account for the inherint thread problems within tkinter.

    TODO: Investigate how to secure this functionality.
    """

    def __init__(self, name=None, target=None, args=None):
        if not name:
            name = target.__name__ + '_' + str(random.randint(1000, 9999))
        self.name = name
        self.target = target
        self.args = args
        self.t = None

    def wrapper(self, args):
        """
        This wraps the threads target allowing us to report closures.
        """
        key = '/thregistry/' + self.name
        running = mc.get(key)
        if not running:  # Check to see if thread is already running.
            mc.set(key, 'active', 30)  # Set running flag.
            print('launching', self.name)
            self.target(*args)  # Launch thread target.
            mc.delete(key)
        else:
            mc.touch(key)  # Refresh key expiry.

    def start(self):
        """
        This launches our wrapped target into a thread.
        """
        self.t = T(target=self.wrapper, name=self.name, args=(self.args,))  # Create thread instance.
        self.t.start()  # Launch thread.

    def join(self, value):
        """
        This performs a join of our target thread.
        """
        self.t.join(value)  # Join thread.


def test():
    """
    This is a test function for the above class.
    """
    def runner():
        """
        This runs a test loop
        """
        while True:
            print('running!')
            time.sleep(1)

    th = Thread(name='runner', target=runner, args=())
    th.start()
