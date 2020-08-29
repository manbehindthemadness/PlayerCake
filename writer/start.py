"""
This is the main program loop for the writer application.
"""

from guizero import App, Box, Text

app = App()
box = Box(app, width=150, height=150)
box.bg = "red"
box.border = True

text = Text(box, text="hello")
app.display()