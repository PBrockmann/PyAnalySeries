import matplotlib.pyplot as plt
import numpy as np

import matplotlib
matplotlib.use("Qt5Agg")

print(matplotlib.get_backend())

fig, ax = plt.subplots(1, 1)

left_margin = 100
right_margin = 50
top_margin = 50
bottom_margin = 50

x1 = np.linspace(0, 10, 100)
y1 = np.sin(x1)

line, = ax.plot(x1, y1)
ax.set_xlabel('x label')
ax.set_ylabel('y label')

width, height = fig.get_size_inches() * fig.dpi
print(width, height, fig.dpi)

fig.subplots_adjust(
    left = left_margin / width,
    right = 1 - right_margin / width,
    top = 1 - top_margin / height,
    bottom = bottom_margin / height,
    wspace = None,
    hspace = 0.5
)

plt.show()
