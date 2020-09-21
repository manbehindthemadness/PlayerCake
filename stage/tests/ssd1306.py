"""
# Copyright (c) 2017 Adafruit Industries
# Author: Tony DiCola & James DeVito
"""
from collections import OrderedDict
# from luma.core.render import canvas
# from PIL import ImageFont
# import sys
# import logging
# from luma.core import cmdline, error
# import os
#
#
# # logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)-15s - %(message)s'
# )
# # ignore PIL debug messages
# logging.getLogger('PIL').setLevel(logging.ERROR)
#
#
# def display_settings(args):
#     """
#     Display a short summary of the settings.
#     :rtype: str
#     """
#     iface = ''
#     display_types = cmdline.get_display_types()
#     if args.display not in display_types['emulator']:
#         iface = 'Interface: {}\n'.format(args.interface)
#
#     lib_name = cmdline.get_library_for_display_type(args.display)
#     if lib_name is not None:
#         lib_version = cmdline.get_library_version(lib_name)
#     else:
#         lib_name = lib_version = 'unknown'
#
#     import luma.core
#     version = 'luma.{} {} (luma.core {})'.format(
#         lib_name, lib_version, luma.core.__version__)
#
#     return 'Version: {}\nDisplay: {}\n{}Dimensions: {} x {}\n{}'.format(
#         version, args.display, iface, args.width, args.height, '-' * 60)
#
#
# def get_device(actual_args=None):
#     """
#     Create device from command-line arguments and return it.
#     """
#     device = None
#     if actual_args is None:
#         actual_args = sys.argv[1:]
#     parser = cmdline.create_parser(description='PlayerCake Visual Debugger')
#     args = parser.parse_args(actual_args)
#
#     if args.config:
#         # load config from file
#         config = cmdline.load_config(args.config)
#         args = parser.parse_args(config + actual_args)
#
#     # print(display_settings(args))
#
#     # create device
#     try:
#         device = cmdline.create_device(args)
#     except error.Error as e:
#         parser.error(e)
#
#     return device
#
#
# class Display:
#     """
#     This is our debug screen controller.
#     """
#     def __init__(self, controller):
#         """
#         :param controller: Inherit from real time program.
#         :type controller: rt.Start
#         """
#         self.controller = controller
#         self.mode = self.controller.debug_screen_mode
#         self.lines = self.controller.lines
#         self.device = get_device()
#
#     def text(self):
#         """
#         This is the micro-console debug mode.
#
#         {
#             "1": {
#                 "x_pos": 0,
#                 "y_pos": 0,  - This is added by-line into padding.
#                 "message": "Text to display".
#                 "font": "my font here", - Defaults to self.font if empty.
#                 "file": 155, - Defaults to 255 if empty
#             },,
#             "2": {}, - etc....
#         }
#         """
#         font_path = os.path.abspath(
#             os.path.join(
#                 # os.path.dirname(__file__), 'fonts', 'C&C Red Alert [INET].ttf'))
#                 os.path.dirname(__file__), 'fonts', 'code2000.ttf'))
#         font2 = ImageFont.truetype(font_path, 8)
#         font3 = ImageFont.truetype(font_path, 16)
#         lines = list(self.lines)
#         lines.reverse()
#         inc = 7
#         draw = canvas(self.device)
#         for idx, line in enumerate(lines[:7]):
#             # with canvas(self.device) as draw:
#             inc += 7
#             if not idx:
#                 draw.text((0, 0), str(line), font=font3, fill="white")
#             else:
#                 draw.text((0, inc), str(line), font=font2, fill="white")




# def inc(device):
#     """
#     Just a test
#     """
#     font_path = os.path.abspath(
#         os.path.join(
#             # os.path.dirname(__file__), 'fonts', 'C&C Red Alert [INET].ttf'))
#             os.path.dirname(__file__), 'fonts', 'code2000.ttf'))
#     font2 = ImageFont.truetype(font_path, 8)
#     font3 = ImageFont.truetype(font_path, 16)
#     ic = 0
#     while True:
#         with canvas(device) as draw:
#             draw.text((0, 0), str(ic), font=font3, fill="white")
#             # draw.text((0, 8), str(ic), font=font2, fill="white")
#             draw.text((0, 14), str(ic), font=font2, fill="white")
#             draw.text((0, 21), str(ic), font=font2, fill="white")
#             draw.text((0, 28), str(ic), font=font2, fill="white")
#             draw.text((0, 35), str(ic), font=font2, fill="white")
#             draw.text((0, 42), str(ic), font=font2, fill="white")
#             draw.text((0, 49), str(ic), font=font2, fill="white")
#             ic += 1
#
# inc(get_device())