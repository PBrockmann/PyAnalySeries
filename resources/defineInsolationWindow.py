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
        groupbox1.setFixedWidth(600)

        form_layout = QFormLayout()

        #-------------------------------
        # Insolation type dropdown
        self.insolationType_dropdown = QComboBox()
        self.insolationType_dropdown.addItems([
            "Daily insolation",
            "Integrated insolation between 2 true longitudes",
            "Caloric summer insolation",
            "Caloric winter insolation"
        ])
        self.insolationType_dropdown.setCurrentIndex(0)

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
        self.latitude_input.setValue(65)
        self.latitude_input.setSingleStep(5)

        #-------------------------------
        # True longitude #1
        self.trueLongitude1_input = QSpinBox()
        self.trueLongitude1_input.setRange(0, 360)
        self.trueLongitude1_input.setValue(90)
        self.trueLongitude1_input.setSingleStep(5)
        self.trueLongitude1_input.valueChanged.connect(self.updateTrueLongitude2Limit)

        #-------------------------------
        # True longitude #2
        self.trueLongitude2_input = QSpinBox()
        self.trueLongitude2_input.setRange(1, 360)
        self.trueLongitude2_input.setValue(180)
        self.trueLongitude2_input.setSingleStep(5)

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
        self.tstep_input.setSingleStep(1)

        #-------------------------------
        self.timeDirection_dropdown = QComboBox()
        self.timeDirection_dropdown.addItems([
            "Past > 0",
            "Past < 0"
        ])
        self.timeDirection_dropdown.setCurrentIndex(0)

        #-------------------------------
        self.timeUnit_dropdown = QComboBox()
        self.timeUnit_dropdown.addItems([
            "yr",
            "kyr"
        ])
        self.timeUnit_dropdown.setCurrentIndex(1)
        self.timeUnit = self.timeUnit_dropdown.currentText()

        #-------------------------------
        form_layout.addRow("Type:", self.insolationType_dropdown)
        form_layout.addRow("Astronomical solution:", self.solutionAstro_dropdown)
        form_layout.addRow("Solar constant [W/m2]:", self.solar_constant_input)
        form_layout.addRow("Latitude [°]:", self.latitude_input)
        form_layout.addRow("True longitude #1 [°]:", self.trueLongitude1_input)
        form_layout.addRow("True longitude #2 [°]:", self.trueLongitude2_input)
        form_layout.addRow("Time direction:", self.timeDirection_dropdown)
        form_layout.addRow("Time unit:", self.timeUnit_dropdown)
        self.label_tstart = QLabel(f"Start [{self.timeUnit}]:")
        form_layout.addRow(self.label_tstart, self.tstart_input)
        self.label_tend = QLabel(f"End [{self.timeUnit}]:")
        form_layout.addRow(self.label_tend, self.tend_input)
        self.label_tstep = QLabel(f"Step [{self.timeUnit}]:")
        form_layout.addRow(self.label_tstep, self.tstep_input)

        #-------------------------------
        groupbox1.setLayout(form_layout)
        main_layout.addWidget(groupbox1)

        #----------------------------------------------
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.myplot)

        self.insolationType_dropdown.currentIndexChanged.connect(self.parameters_change)
        self.solutionAstro_dropdown.currentIndexChanged.connect(self.delayed_update)
        self.solar_constant_input.valueChanged.connect(self.delayed_update)
        self.latitude_input.valueChanged.connect(self.delayed_update)
        self.trueLongitude1_input.valueChanged.connect(self.delayed_update)
        self.trueLongitude2_input.valueChanged.connect(self.delayed_update)
        self.timeUnit_dropdown.currentIndexChanged.connect(self.timeUnit_change)
        self.tstart_input.valueChanged.connect(self.delayed_update)
        self.tend_input.valueChanged.connect(self.delayed_update)
        self.tstep_input.valueChanged.connect(self.delayed_update)
        self.timeDirection_dropdown.currentIndexChanged.connect(self.delayed_update)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()

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

        self.parameters_change()
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def timeUnit_change(self):

        self.timeUnit = self.timeUnit_dropdown.currentText()
        self.label_tstart.setText(f"Start [{self.timeUnit}]:")
        self.label_tend.setText(f"End [{self.timeUnit}]:")
        self.label_tstep.setText(f"Step [{self.timeUnit}]:")

        if self.timeUnit == 'yr':
            self.tstart_input.blockSignals(True)
            current_value = self.tstart_input.value()
            self.tstart_input.setRange(-101000*1000, 21000*1000)
            self.tstart_input.setValue(current_value * 1000)
            self.tstart_input.setSingleStep(1000)
            self.tstart_input.blockSignals(False)

            self.tend_input.blockSignals(True)
            current_value = self.tend_input.value()
            self.tend_input.setRange(-101000*1000, 21000*1000)
            self.tend_input.setValue(current_value * 1000)
            self.tend_input.setSingleStep(1000)
            self.tend_input.blockSignals(False)

            self.tstep_input.blockSignals(True)
            current_value = self.tstep_input.value()
            self.tstep_input.setRange(1, 1000*1000)
            self.tstep_input.setValue(current_value * 1000)
            self.tstep_input.setSingleStep(1000)
            self.tstep_input.blockSignals(False)

        else:               # kyr
            self.tstart_input.blockSignals(True)
            current_value = self.tstart_input.value()
            self.tstart_input.setRange(-101000, 21000)
            self.tstart_input.setValue(current_value // 1000)
            self.tstart_input.setSingleStep(1)
            self.tstart_input.blockSignals(False)

            self.tend_input.blockSignals(True)
            current_value = self.tend_input.value()
            self.tend_input.setRange(-101000, 21000)
            self.tend_input.setValue(current_value // 1000)
            self.tend_input.setSingleStep(1)
            self.tend_input.blockSignals(False)

            self.tstep_input.blockSignals(True)
            current_value = self.tstep_input.value()
            self.tstep_input.setRange(1, 1000)
            self.tstep_input.setValue(current_value // 1000)
            self.tstep_input.setSingleStep(1)
            self.tstep_input.blockSignals(False)

        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def updateTrueLongitude2Limit(self, value):
        self.trueLongitude2_input.setMinimum(value + 1)

    #---------------------------------------------------------------------------------------------
    def parameters_change(self):
        if self.insolationType_dropdown.currentIndex() == 0:
            self.trueLongitude1_input.setEnabled(True)
            self.trueLongitude2_input.setEnabled(False)
        elif self.insolationType_dropdown.currentIndex() == 1:
            self.trueLongitude1_input.setEnabled(True)
            self.trueLongitude2_input.setEnabled(True)
        elif self.insolationType_dropdown.currentIndex() == 2:
            self.trueLongitude1_input.setEnabled(False)
            self.trueLongitude2_input.setEnabled(False)
        elif self.insolationType_dropdown.currentIndex() == 3:
            self.trueLongitude1_input.setEnabled(False)
            self.trueLongitude2_input.setEnabled(False)

        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def delayed_update(self):
        self.status_bar.showMessage('Waiting', 1000)
        self.update_timer.start(1000)

    #---------------------------------------------------------------------------------------------
    def myplot(self):

        solar_constant = self.solar_constant_input.value()
        latitude = self.latitude_input.value()
        trueLongitude1 = self.trueLongitude1_input.value()
        trueLongitude2 = self.trueLongitude2_input.value()
        t_start = self.tstart_input.value()
        t_end = self.tend_input.value()
        t_step = self.tstep_input.value()

        if self.timeDirection_dropdown.currentIndex() == 0:
            t_direction = -1
        else:
            t_direction = 1

        if self.timeUnit == 'yr':
            t = np.arange(t_start, (t_end+1), t_step)/1000
        else:
            print((t_start, (t_end+1), t_step))
            t = np.arange(t_start, t_end+1, t_step)

        deg_to_rad = np.pi/180.
        
        astro_params = eval(f"astro.Astro{self.solutionAstro_dropdown.currentText()}()")
        ecc = astro_params.eccentricity(t)
        pre = astro_params.precession_angle(t)
        obl = astro_params.obliquity(t)

        insoValues = np.empty(len(t))
        if self.insolationType_dropdown.currentIndex() == 0:
            for i in range(len(t)): 
                insoValues[i] = solar_constant * \
                            inso.inso_daily_radians(
                                    trueLongitude1*deg_to_rad,
                                    latitude*deg_to_rad, 
                                    obl[i], 
                                    ecc[i], 
                                    pre[i])
        elif self.insolationType_dropdown.currentIndex() == 1:
            for i in range(len(t)): 
                insoValues[i] = solar_constant * \
                            inso.inso_mean_radians(
                                    trueLongitude1*deg_to_rad,
                                    trueLongitude2*deg_to_rad,
                                    latitude*deg_to_rad, 
                                    obl[i], 
                                    ecc[i], 
                                    pre[i])
        elif self.insolationType_dropdown.currentIndex() == 2:
            for i in range(len(t)): 
                insoValues[i] = solar_constant * \
                            inso.inso_caloric_summer_NH(
                                                    latitude*deg_to_rad, 
                                                    obl[i], 
                                                    ecc[i], 
                                                    pre[i])
        elif self.insolationType_dropdown.currentIndex() == 3:
            for i in range(len(t)): 
                insoValues[i] = solar_constant * \
                            inso.inso_caloric_winter_NH(
                                                    latitude*deg_to_rad, 
                                                    obl[i], 
                                                    ecc[i], 
                                                    pre[i])

        if self.timeUnit == 'yr':
            self.index = t * t_direction * 1000
        else:
            self.index = t * t_direction
        self.values = insoValues

        ax = self.interactive_plot.axs[0]

        ax.clear()
        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)

        color = "darkorange"
        line1, = ax.plot(self.index, self.values, linewidth=0.5, color=color)
        points1 = ax.scatter(self.index, self.values, s=5, marker='o', color=color, visible=False)
        ax.line_points_pairs.append((line1, points1))

        ax.set_xlabel(self.timeUnit)
        ax.set_ylabel("Insolation [W/m2]")
        ax.autoscale()

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()
        self.status_bar.showMessage('Updated', 1000)

    #---------------------------------------------------------------------------------------------
    def import_serie(self):

        if self.insolationType_dropdown.currentIndex() == 0:
            # "Daily insolation",
            history = f'Insolation serie "{self.insolationType_dropdown.currentText()}" with parameters:' + \
                        '<ul>' + \
                        f'<li>Solar constant [W/m2]: {self.solar_constant_input.value()}' + \
                        f'<li>Latitude [°]: {self.latitude_input.value()}' + \
                        f'<li>True longitude [°]: {self.trueLongitude1_input.value()}' + \
                        '</ul>'
            shortName = "Daily insolation [W/m2]"
        elif self.insolationType_dropdown.currentIndex() == 1:
            # "Integrated insolation between 2 true longitudes",
            history = f'Insolation serie "{self.insolationType_dropdown.currentText()}" with parameters:' + \
                        '<ul>' + \
                        f'<li>Solar constant [W/m2]: {self.solar_constant_input.value()}' + \
                        f'<li>Latitude [°]: {self.latitude_input.value()}' + \
                        f'<li>True longitude #1 [°]: {self.trueLongitude1_input.value()}' + \
                        f'<li>True longitude #2 [°]: {self.trueLongitude2_input.value()}' + \
                        '</ul>'
            shortName = "Integrated insolation [W/m2]"
        elif self.insolationType_dropdown.currentIndex() >= 1:
            # "Caloric summer insolation",
            # "Caloric winter insolation"
            history = f'Insolation serie "{self.insolationType_dropdown.currentText()}" with parameters:' + \
                        '<ul>' + \
                        f'<li>Solar constant [W/m2]: {self.solar_constant_input.value()}' + \
                        f'<li>Latitude [°]: {self.latitude_input.value()}' + \
                        '</ul>'
            shortName = f"{self.insolationType_dropdown.currentText()} [W/m2]"

        serieDict = {
            'Id': generate_Id(), 
            'Type': 'Serie', 
            'Name': '', 
            'X': 'years',
            'Y': shortName,
            'Y axis inverted': False,
            'Color': generate_color(),
            'History': history,
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

