import sys
import matplotlib
matplotlib.use("Qt5Agg")

from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

fig, ax = plt.subplots()

left_margin = 50
right_margin = 50
top_margin = 50
bottom_margin = 50

ax.plot([0, 1, 2, 3], [0, 1, 4, 9])  # Exemple de graphique
ax.set_xlabel('x label')
ax.set_ylabel('y label')

app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Matplotlib avec PyQt")

central_widget = QWidget()
layout = QVBoxLayout(central_widget)

width, height = fig.get_size_inches() * fig.dpi

fig.subplots_adjust(
    left = left_margin / width,
    right = 1 - right_margin / width,
    top = 1 - top_margin / height,
    bottom = bottom_margin / height,
    wspace = None,
    hspace = 0.5
)

canvas = FigureCanvas(fig)
layout.addWidget(canvas)

window.setCentralWidget(central_widget)
window.show()
sys.exit(app.exec())

