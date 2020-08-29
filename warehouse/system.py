"""
This file holds code for reading system status properties (such as CPU temp)
"""

from subprocess import PIPE, Popen
import psutil


def get_cpu_temperature():
    """get cpu temperature using vcgencmd"""
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    output = output.decode("utf8")
    return float(output[output.index('=') + 1:output.rindex("'")])


def get_system_stats():
    """
    Here is where we gather various system statistics.
    """
    output = dict()
    output['CPU_LOAD'] = psutil.cpu_percent()
    output['CPU_TIMES'] = psutil.cpu_times()
    output['BOOT_TIME'] = psutil.boot_time()
    output['DISK_IO'] = psutil.disk_usage('/')
    output['SWAP_MEMORY'] = psutil.swap_memory()
    output['VIRTUAL_MEMORY'] = psutil.virtual_memory()
    sensors = dict()
    sensors['TEMPS'] = psutil.sensors_temperatures()
    sensors['FANS'] = psutil.sensors_fans()
    sensors['BATTERY'] = psutil.sensors_battery()
    output['SENSORS'] = sensors
    return output


def system_command(params):
    """
    Use this to execute a system level command.

    NOTE: Use with caution.
    :param params: List of commands and args to execute.
    :type params: list
    """
    process = Popen(params, stdout=PIPE)
    output, _error = process.communicate()
    output = output.decode("utf8")
    return output
