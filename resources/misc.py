
import uuid
import random

from matplotlib import cm

from PyQt5.QtGui import QColor 

#========================================================================================
def generate_Id():
    return f"Id-{str(uuid.uuid4())[:8].upper()}"

#========================================================================================
def generate_color(exclude_color=None):
    tab20_colors = [QColor(*(int(c * 255) for c in cm.tab20(i)[:3])).name() for i in range(20)]
    if exclude_color in tab20_colors:
        tab20_colors.remove(exclude_color)
    return random.choice(tab20_colors)

#========================================================================================
def append_to_htmlText(text, new_value):
    if text:
        text += "<br>"
    text += new_value
    return text 

#========================================================================================
def cleanList(aList):
    return [x for x in aList if x != '']

