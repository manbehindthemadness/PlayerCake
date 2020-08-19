"""
This is where we will keep the code used to update various displays used across the platforms.
"""

from collections import OrderedDict
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


class SSD1306:
    """
    Display driver for the SSD1306 OLED display.
    """
    def __init__(self):
        self.i2c = busio.I2C(SCL, SDA)
        self.disp = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c)
        # Clear display
        self.disp.fill(0)
        self.disp.show()
        # Init display.
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new("1", (self.width, self.height))
        self.image_draw = ImageDraw.Draw(self.image)
        self.image_draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        # Set x padding.
        self.x = 0
        self.fill = 255
        self.padding = -2
        self.top = self.padding
        self.bottom = self.height - self.padding
        self.font = ImageFont.load_default()

    def text_draw(self, items):
        """
        This draws some text onto the screen:

        {
            "1": {
                "x_pos": 0,
                "y_pos": 0,  - This is added by-line into padding.
                "message": "Text to display".
                "font": "my font here", - Defaults to self.font if empty.
                "file": 155, - Defaults to 255 if empty
            },,
            "2": {}, - etc....
        }

        :param items: This is a dictionary of the various things we want to draw
        :type items: dict
        """
        # Set defaults:
        defaults = {
            'x_pos': 'self.x',
            'y_pos': 'self.top * (cnt * 8)',
            'message': 'missing text...',
            'font': 'self.font',
            'fill': 'self.fill,'
        }

        lines = OrderedDict(sorted(items.items()))
        for cnt, line in enumerate(lines):
            params = lines[line]
            for param in params:
                if not params[param]:
                    params[param] = defaults[param]
            args = (
                tuple((eval(params['x_pos']), eval(params['y_pos']))),
                params['message'],
                eval(params['font']),
                eval(params['fill'])
            )
            print(
                args
            )
            self.image_draw.text(
                tuple((eval(params['x_pos']), eval(params['y_pos']))),
                params['message'],
                font=eval(params['font']),
                fill=eval(params['fill'])
            )
            self.disp.image(self.image)
            self.disp.show()


# Test logic
# SSD1306().text_draw({'1': {'x_pos': '', 'y_pos': '', 'message': 'hey!', 'font': '', 'fill': ''}})
