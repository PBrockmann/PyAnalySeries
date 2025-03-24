
import uuid
import random
import numpy as np

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
def addNanList(aList):
    return [np.nan if x == '' else x for x in aList]        # Handle missing values

#========================================================================================
def cleanSpaceList(aList):
    return [x for x in aList if x != '']

#========================================================================================
def is_open(file):
    try:
        with open(file, "r+") as f:
            return False
    except IOError:
        return True

