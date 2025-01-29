from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt

from .misc import *
from .interactivePlot import interactivePlot

from .insolation import inso
from .insolation import astro

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
        groupbox1.setFixedWidth(400)

        form_layout = QFormLayout()

        #-------------------------------
        # Astronomical solution dropdown
        self.solutionAstro_dropdown = QComboBox()
        self.solutionAstro_dropdown.addItems(["Berger1978", "Laskar2004"])
        self.solutionAstro_dropdown.setCurrentIndex(1)
        
        #-------------------------------
        # Solar constant input
        self.solar_constant_input = QSpinBox()
        self.solar_constant_input.setRange(1000, 1500)
        self.solar_constant_input.setValue(1365)
        self.solar_constant_input.setSingleStep(5)

        #-------------------------------
        # Latitude slider
        self.latitude_input = QSpinBox()
        self.latitude_input.setRange(-90, 90)
        self.latitude_input.setValue(0)
        self.latitude_input.setSingleStep(5)

        #-------------------------------
        # True longitude slider
        self.trueLongitude_input = QSpinBox()
        self.trueLongitude_input.setRange(0, 360)
        self.trueLongitude_input.setValue(0)
        self.trueLongitude_input.setSingleStep(5)

        #-------------------------------
        # Time inputs (Start, End, Step)
        self.tstart_input = QSpinBox()
        self.tstart_input.setRange(-101000, 21000)
        self.tstart_input.setValue(-1000)
        self.tstart_input.setSingleStep(1000)
        
        self.tend_input = QSpinBox()
        self.tend_input.setRange(-101000, 21000)
        self.tend_input.setValue(0)
        self.tend_input.setSingleStep(1000)

        self.tstep_input = QSpinBox()
        self.tstep_input.setRange(1, 1000)
        self.tstep_input.setValue(1)

        form_layout.addRow("Astronomical solution:", self.solutionAstro_dropdown)
        form_layout.addRow("Solar constant [W/m2]:", self.solar_constant_input)
        form_layout.addRow("Latitude [°]:", self.latitude_input)
        form_layout.addRow("True longitude [°]:", self.trueLongitude_input)
        form_layout.addRow("Start [t]:", self.tstart_input)
        form_layout.addRow("End [t]:", self.tend_input)
        form_layout.addRow("Step [t]:", self.tstep_input)

        #-------------------------------
        groupbox1.setLayout(form_layout)
        main_layout.addWidget(groupbox1)

        self.solutionAstro_dropdown.currentIndexChanged.connect(self.myplot)
        self.solar_constant_input.valueChanged.connect(self.myplot)
        self.latitude_input.valueChanged.connect(self.myplot)
        self.trueLongitude_input.valueChanged.connect(self.myplot)
        self.tstart_input.valueChanged.connect(self.myplot)
        self.tend_input.valueChanged.connect(self.myplot)
        self.tstep_input.valueChanged.connect(self.myplot)

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

        solar_constant = self.solar_constant_input.value()
        latitude = self.latitude_input.value()
        trueLongitude = self.trueLongitude_input.value()
        t_start = self.tstart_input.value()
        t_end = self.tend_input.value()
        t_step = self.tstep_input.value()

        t = np.arange(t_start, t_end+1, t_step)

        deg_to_rad = np.pi/180.
        
        astro_params = eval(f"astro.Astro{self.solutionAstro_dropdown.currentText()}()")
        ecc = astro_params.eccentricity(t)
        pre = astro_params.precession_angle(t)
        obl = astro_params.obliquity(t)

        inso_daily = np.empty(len(t))
        for i in range(len(t)):
            inso_daily[i] = solar_constant * \
                            inso.inso_daily_radians(inso.trueLongitude(trueLongitude*deg_to_rad, ecc[i], pre[i]), 
                                                    latitude*deg_to_rad, 
                                                    obl[i], 
                                                    ecc[i], 
                                                    pre[i])

        self.index = t
        self.values = inso_daily 

        self.interactive_plot.axs[0].clear()
        self.interactive_plot.axs[0].plot(self.index, self.values, linewidth=0.5)

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def import_serie(self):

        serieDict = {
            'Id': generate_Id(), 
            'Type': 'Serie', 
            'Name': '', 
            'X': 'years',
            'Y': 'Daily insolation [w/m2]',
            'Y axis inverted': False,
            'Color': generate_color(),
            'History': f'Insolation daily serie with parameters:' + 
                        '<ul>' +
                        f'<li>Solar constant [W/m2]: {self.solar_constant_input.value()}' +
                        f'<li>Latitude [°]: {self.latitude_input.value()}' +
                        f'<li>True longitude [°]: {self.trueLongitude_input.value()}' +
                        '</ul>',
            'Comment': '',
            'Serie': pd.Series(self.values, index=self.index),
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

