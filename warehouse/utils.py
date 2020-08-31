"""
This is where we house general utilities.
"""
import datetime
import re
from colour import Color
from PIL import Image
from resizeimage import resizeimage
from os import path
from pathlib import Path


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
    file = open(filename)
    return file.read()


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


def file_rename(name, file):
    """
    This appends 'name' to a filename 'file' whilst preserving the extension.
    :type name: str
    :type file: str
    :rtype: str
    """
    pa, fi = file.rsplit('.', 1)
    name += '.'
    return pa + name + fi


def file_exists(file):
    """
    Checks to see if a specific file exists.
    :type file: str
    :rtype: bool
    """
    return path.exists(file)


def image_resize(x, y, image, x_percent, y_percent, preserve_aspect=True):
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
    :return: Resized image's file name.
    :rtype: str
    """
    base = Path.cwd()
    x_pix = percent_of(x, x_percent)
    y_pix = percent_of(y, y_percent)
    tp = base / Path('img/resize')
    tfn = tp / file_rename(str(x_pix) + '_' + str(y_pix), image)
    # print('target', tfn)
    if not file_exists(tfn):
        sp = base / Path('img/base')
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
    return tfn
