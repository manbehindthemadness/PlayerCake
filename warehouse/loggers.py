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
    if settings.debug:
        print(*err)


def tprint(settings, err):
    """
    Just like above, but for threads
    """
    if settings.debug_threads:
        dprint(settings, err)
