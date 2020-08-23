"""
This is where we house general utilities.
"""


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
