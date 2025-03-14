import sys

import matplotlib.pyplot as plt

from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from class1 import myplot

#========================================================
def close():
    print('close')
    app.quit()

#========================================================
app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Matplotlib avec PyQt")

plot1 = myplot()
fig = plot1.fig
ax = plot1.ax

ax.plot([0, 1, 2, 3], [0, 1, 4, 9])
ax.set_xlabel('x label')
ax.set_ylabel('y label')

central_widget = QWidget()
layout = QVBoxLayout(central_widget)

canvas = FigureCanvas(fig)
layout.addWidget(canvas)

button_layout = QHBoxLayout()
save_button = QPushButton("Save")
close_button = QPushButton("Close")
close_button.clicked.connect(close)
button_layout.addStretch()

button_layout.addWidget(save_button)
button_layout.addWidget(close_button)
layout.addLayout(button_layout)

window.setCentralWidget(central_widget)
window.show()

sys.exit(app.exec())

