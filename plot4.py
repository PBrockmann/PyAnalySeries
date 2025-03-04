import matplotlib.pyplot as plt
import numpy as np

import matplotlib
matplotlib.use("Qt5Agg")

plt.rcParams['figure.dpi'] = 100

from resources.interactivePlot import interactivePlot

interactive_plot = interactivePlot()

#interactive_plot.left_margin = 200

ax = interactive_plot.axs[0]


x1 = np.linspace(0, 10, 100)
y1 = np.sin(x1)

line, = ax.plot(x1, y1)
ax.set_xlabel('x label')
ax.set_ylabel('y label')

plt.show()
