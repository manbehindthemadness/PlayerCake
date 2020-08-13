"""
This is where we house general utilities.
"""


def average(lst):
    """
    Avrages the values in a list.
    """
    return sum(lst) / len(lst)


class fade:
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
        data_len = len(values)
        if data_len >= depth:
            del values[0]
        if value:
            values.append(value)
        return_value = 0.0
        if values:
            return_value = average(values)

        return [return_value, values]
