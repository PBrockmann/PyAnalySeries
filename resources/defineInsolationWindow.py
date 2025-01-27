from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt

from .misc import *
from .interactivePlot import interactivePlot

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineInsolationWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, open_insolationWindow, add_item_tree_widget):
        super().__init__()

        self.open_insolationWindow = open_insolationWindow
        self.add_item_tree_widget = add_item_tree_widget

        title = 'Define insolation serie'
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters')
        groupbox1_layout = QVBoxLayout()
        groupbox1.setFixedHeight(150)

        layout_s1 = QHBoxLayout()

        label_s1 = QLabel('Latitude on the Earth :')
        self.spin_box = QSpinBox(self)
        self.spin_box.setRange(-90, 90)
        self.spin_box.setSingleStep(1)
        self.spin_box.setValue(60)
        self.spin_box.setFixedWidth(50)
        layout_s1.addWidget(label_s1)
        layout_s1.addWidget(self.spin_box)
        layout_s1.addStretch()

        groupbox1_layout.addLayout(layout_s1)
        groupbox1_layout.addStretch()

        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()
        self.myplot()

        main_layout.addWidget(self.interactive_plot.fig.canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        self.import_button = QPushButton("Import serie", self)
        self.close_button = QPushButton("Close", self)
        button_layout.addStretch()

        button_layout.addWidget(self.import_button)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.import_button.clicked.connect(self.import_serie)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        #self.status_bar.showMessage('Ready', 5000)

    #---------------------------------------------------------------------------------------------
    def myplot(self):

        self.interactive_plot.axs[0].plot([1,2,3], [1,2,3])

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def import_serie(self):

        index = []
        values = []

        serieDict = {
            'Id': generate_Id(), 
            'Type': 'Serie', 
            'Name': '', 
            'X': 'aaaaa',
            'Y': 'bbbbb',
            'Y axis inverted': False,
            'Color': generate_color(),
            'History': 'Insolation serie',
            'Comment': '',
            'Serie': pd.Series(values, index=index),
            }

        self.add_item_tree_widget(None, serieDict)          # will be added on parent from current index

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.open_insolationWindow.pop('123456', None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(parent, item):
        print('handle', parent, item)

    app = QApplication([])

    Id_insolationWindow = '1234'
    open_insolationWindow = {}

    insolationWindow = defineInsolationWindow(open_insolationWindow, handle_item)
    open_insolationWindow[Id_insolationWindow] = defineInsolationWindow
    insolationWindow.show()

    sys.exit(app.exec_())

