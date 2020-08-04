"""
This file holds code for reading system status properties (such as CPU temp)
"""

from subprocess import PIPE, Popen


def get_cpu_temperature():
    """get cpu temperature using vcgencmd"""
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    output = output.decode("utf8")
    return float(output[output.index('=') + 1:output.rindex("'")])
