"""
This is where we will sore various debug loggers.
"""


def dprint(settings, err):
    """
    The simplest debug logger.

    :param settings: Instance of settings file.
    :type settings: module
    :param err: Message to print.
    :type err: tuple
    :return: Nothing.
    """
    if settings.Debug:
        print(*err)


def tprint(settings, err):
    """
    Just like above, but for threads
    """
    if settings.Debug_Threads:
        dprint(settings, err)
