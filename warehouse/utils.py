"""
This is where we house general utilities.
"""
import datetime
import re
import os
from colour import Color
from PIL import Image
from resizeimage import resizeimage
from os import path, rename, remove
from pathlib import Path
import configparser


def to_color(limit_low, limit_high):
    """
    This converts a number into an RGB tuple this it defined within the limits
    """
    limit_high += 1
    blue = Color("blue")
    values = dict()
    colors = list(blue.range_to(Color("red"), abs(limit_high - limit_low)))
    labels = list(range(limit_low, limit_high))
    for idx, color in zip(labels, colors):
        values[idx] = Color.get_rgb(color)
    return values


def average(lst):
    """
    Avrages the values in a list.
    """
    return sum(lst) / len(lst)


class Fade:
    """
    This smoothes a series of values by avaraging them ofer a set number of iterations.
    """
    def __new__(cls, depth, values, value):
        """
        :param depth: The number of samples to use.
        :type depth: int
        :param values: Array of values to evaluate.
        :type values: list
        :param value: The latest sampled value.
        :type value: int, float
        :Return: Updated array and values.
        :rtype: list
        """
        data_len = len(values)  # Check the length of incoming values.
        if data_len >= depth:  # Trim value if required.
            del values[0]
        if value:  # Add latest value.
            values.append(value)
        return_value = 0.0
        if values:
            return_value = average(values)

        return [return_value, values]


def check_dict(_dict, key):
    """
    Checks to see if a key is in a dictionary and adds it if missing.
    :param _dict: Target dictionary.
    :type _dict: dict
    :param key: Value to locate.
    :type key: str
    :rtype: dict
    """
    if key not in _dict.keys():
        _dict[key] = dict()
    return _dict[key]


def update_dict(old, new):
    """
    Updates the contents of the old dictionary with the contents of the new.
    :type old: dict
    :type new: dict
    :rtype: dict
    """
    n_keys = new.keys()
    o_keys = old.keys()
    for n_key in n_keys:  # Update missing keys.
        if n_key not in o_keys:
            old[n_key] = new[n_key]
    for n_key in new:  # Iterate and compare the remainder.
        if new[n_key] is dict:
            old[n_key] = update_dict(old[n_key], new[n_key])
        else:
            if old[n_key] != new[n_key]:
                old[n_key] = new[n_key]
    return old


def open_file(filename):
    """
    Opens a text file.
    :param filename: File to open.
    :type filename: Str
    :return: Contents of file.
    :rtype: str
    """
    file = open(filename, 'r+')
    return file.read()


def update_setting(filename, section, setting, value, merge=False):
    """
    Here we are able to update a settings file's contents, this is for deploying new settings.

    NOTE: THis will create a file if it's not present.
    """
    def fileswap(file):
        """
        Does a silly musical chairs with the files to work around the update limitation.
        """
        with open(file + '.new', "w") as fh:
            config.write(fh)
        rename(file, file + "~")
        rename(file + ".new", file)
        remove(file + "~")

    if not os.path.exists(filename):  # Create settings file if it doesn't exist.
        os.mknod(filename)
    config = configparser.ConfigParser()  # Load config parser.
    config.read(filename, encoding='utf-8-sig')  # Read settings file.
    try:
        if merge:
            try:
                sett = config.get(section, setting)
                # print(type(sett))
                if isinstance(sett, dict) or isinstance(sett, list):
                    config.set(section, setting, value)  # Save setting value.
            except configparser.NoOptionError:  # Check for missing setting, add if needed.
                config.set(section, setting, value)  # Save setting value.
        else:
            config.set(section, setting, value)  # Save setting value.
        fileswap(filename)
    except configparser.NoSectionError:  # Check for missing section, add if needed.
        config.add_section(section)
        fileswap(filename)
        config = update_setting(filename, section, setting, value)  # Loop to go back and add settings to the newly added section.
    return config


class BuildSettings:
    """
    This constructs a reloadable settings module.
    """
    def __init__(self, filename, defaults=None, pth=''):
        self.config = configparser.ConfigParser()
        self.path = pth
        self.filename = self.path + '/' + filename
        # if not os.path.exists(self.filename):
        #     self.filename = file_rename(defaults, self.filename)
        print(self.filename)
        self.settings = dict()
        self.defaults = defaults
        self.default_settings = dict()
        self.upgrade()

    def load(self, defaults=None):
        """
        Loads or reloads the settings file.
        """
        file = self.filename
        # print(file)
        store = self.settings
        if defaults:
            file = defaults
            store = self.default_settings
        self.config.read(file, encoding='utf-8-sig')
        for section in self.config.sections():
            for (key, val) in self.config.items(section):
                # print(key, val)
                store[key] = val
                val = val.replace('\n', '')
                try:
                    exec('self.' + key + ' = eval("' + val + '")')
                except (NameError, SyntaxError):
                    exec('self.' + key + ' = "' + val + '"')
                # exec('print(self.' + key + ', type(self.' + key + '))')
        return self

    def save(self, upgrade=False):
        """
        Saves the current settings model to file.
        """
        if upgrade:
            self.load()
            store_old = self.settings
            # print(store_old)
            store = self.default_settings
        else:
            store_old = None
            store = self.settings
        for key in store:
            if upgrade:
                # print(store_old.keys())
                if key in store_old.keys():
                    try:
                        storeset = eval(store[key])
                        oldstoreset = eval(store_old[key])
                    except (NameError, SyntaxError):
                        storeset = store[key]
                        oldstoreset = store_old[key]
                    if isinstance(storeset, dict):  # Update dicts.
                        try:
                            # print('updating dict')
                            storeset = update_dict(oldstoreset, storeset)
                            # print(storeset)
                        except KeyError:
                            # print('key error')
                            pass
                    elif isinstance(storeset, list):  # Update lists.
                        for item in storeset:
                            if item not in oldstoreset:
                                oldstoreset.append(item)
                        storeset = oldstoreset
                    store[key] = str(storeset)
                else:
                    print(key, 'not in settings')
            update_setting(
                self.filename,
                'settings',
                key,
                store[key],
                upgrade
            )
        self.load()
        return self

    def add(self, setting, value):
        """
        This will add a setting into our setup.
        """
        if setting in self.settings.keys():
            raise KeyError
        else:
            self.settings[setting] = value
            self.save()
        return self

    def upgrade(self):
        """
        This takes any new settings from the defaults file and merges them into settings.ini.
        """
        self.load(self.defaults)
        self.save(upgrade=True)
        return self

    def set(self, setting, value=''):
        """
        This changes a specific setting value.
        """
        if not value:
            exec('self.settings[setting] = str(self.' + setting + ')')
        else:
            self.settings[setting] = str(value)
        return self


def get_time_secs(timestamp):
    """
    We use this for an easy check to see how old a string timestamp is in seconds.

    NOTE: use datetime.datetime.utcnow with '%Y-%m-%d %H:%M:%S.%f' format.

    :param timestamp:
    :type timestamp: str
    :rtype: float
    """
    seconds = (  # Compare heartbeat times.
            datetime.datetime.utcnow() - datetime.datetime.strptime(
                timestamp, '%Y-%m-%d %H:%M:%S.%f'
            )
    ).total_seconds()
    return seconds


def split_string(string):
    """
    This splits a sring at any non-alphanumeric chars.
    """
    return re.split('[^a-zA-Z]', string)


def ceiling(x):
    """
    Generic math method (rounds up int's instead of down)
    """
    n = int(x)
    return n if n - 1 < x <= n else n + 1


def percent_of(percent, whole, use_float=False):
    """
    Generic math method
    """
    if not percent or not whole:
        result = 0
    else:
        result = (percent * whole) / 100.0
        if not use_float:
            result = ceiling(result)
    return result


def percent_in(part, whole, use_float=False):
    """
    Generic math method
    """
    if not whole:
        result = 0
    else:
        result = 100 * part / whole
        if not use_float:
            result = ceiling(result)
    return result


def file_rename(name, file, reverse=False):
    """
    This appends 'name' to a filename 'file' whilst preserving the extension.
    :type name: str
    :type file: str
    :type reverse: bool
    :rtype: str
    """
    pa, fi = file.rsplit('.', 1)
    if reverse:
        pa += '.'
        result = name + pa + fi
    else:
        name += '.'
        result = pa + name + fi
    return result


def file_exists(file):
    """
    Checks to see if a specific file exists.
    :type file: str
    :rtype: bool
    """
    return path.exists(file)


def image_resize(x, y, image, x_percent, y_percent, preserve_aspect=True, folder_add=False, raw=False):
    """
    This resizes images to a percentage of x and y and saves it to the /img folder
    This skips the action if the resized file already exists.

    https://pypi.org/project/python-resize-image/
    libjpeg-turbo-devel

    :param x: Layout x size in pixels.
    :type x: int
    :param y: Layout y size in pixels.
    :type y: int
    :param image: Filename of the base image.
    :type image: str
    :param x_percent: The x percentags of the output image.
    :type x_percent: int, float
    :param y_percent: The y percentage of the output image.
    :type y_percent: int, float
    :param preserve_aspect: Toggles preservation of the aspect ratio.
    :type preserve_aspect: bool
    :param folder_add: This adds a subfolder to the source path.
    :type folder_add: bool, str
    :param raw: Override folder locations.
    :type raw: bool

    :return: Resized image's file name.
    :rtype: str
    """
    base = Path.cwd()
    x_pix = percent_of(x, x_percent)
    y_pix = percent_of(y, y_percent)
    tp = base / Path('img/resize')

    tfn = tp / file_rename(str(x_pix) + '_' + str(y_pix), image)
    # print('target', tfn)
    if not file_exists(tfn) or raw:
        sp = base / Path('img/base')
        if folder_add:
            sp = base / Path('img/base/' + folder_add)
            if raw:
                sp = Path(folder_add)
                tfn = Path(image)

        sfn = sp / image
        # print('source', sfn)
        if file_exists(sfn):
            img = Image.open(sfn)
            if preserve_aspect:
                img = resizeimage.resize_contain(img, [x_pix, y_pix])
            else:
                img = resizeimage.resize_cover(img, [x_pix, y_pix], validate=False)
            img.save(tfn, img.format)
        else:
            raise FileNotFoundError
        print(sfn, tfn)
    return tfn.as_posix()
