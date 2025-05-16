from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from .misc import *
from .interactivePlot import interactivePlot

from .insolation import inso
from .insolation import astro

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineInsolationAstroSerieWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, open_insolationAstroSerieWindow, add_item_tree_widget):
        super().__init__()

        self.open_insolationAstroSerieWindow = open_insolationAstroSerieWindow
        self.add_item_tree_widget = add_item_tree_widget

        title = 'Define insolation / astromical serie'
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        col_layout = QHBoxLayout()

        #----------------------------------------------
        col1_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters :')

        form_layout = QFormLayout()

        #-------------------------------
        # Insolation type dropdown
        self.plotType_dropdown = QComboBox()
        self.plotType_dropdown.addItems([
            "Eccentricity",
            "Obliquity",
            "Precession angle",
            "Precession parameter",
            "Daily insolation",
            "Integrated insolation between 2 true longitudes",
            "Caloric summer insolation",
            "Caloric winter insolation"
        ])
        self.plotType_dropdown.insertSeparator(4)
        self.plotType_dropdown.setCurrentText("Daily insolation")

        #-------------------------------
        # Astronomical solution dropdown
        self.solutionAstro_dropdown = QComboBox()
        self.solutionAstro_dropdown.addItems(["Berger1978", 
                                              "Laskar1993_01", "Laskar1993_11", 
                                              "Laskar2004",
                                              "Laskar2010a", "Laskar2010b", "Laskar2010c", "Laskar2010d", 
                                              ])
        self.solutionAstro_dropdown.setCurrentText("Laskar2004")
        
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
        # Time direction
        self.timeConvention_dropdown = QComboBox()
        self.timeConvention_dropdown.addItems([
            "Past < 0",
            "Past > 0",
        ])
        self.timeConvention_dropdown.setCurrentIndex(0)
        self.t_convention = 1

        #-------------------------------
        # Time inputs (Start, End, Step)
        self.tstart_input = QSpinBox()
        lim1 = -101000                         # Range for Laskar2004
        lim2 = 21000
        self.tstart_input.setRange(min(lim1, lim2), max(lim1, lim2))
        self.tstart_input.setValue(-1000)
        self.tstart_input.setSingleStep(1000)
        self.tstart_input.setToolTip(f"Choose a value between {min(lim1, lim2)} and {max(lim1, lim2)}")
        
        self.tend_input = QSpinBox()
        self.tend_input.setRange(min(lim1, lim2), max(lim1, lim2))
        self.tend_input.setValue(0)
        self.tend_input.setSingleStep(1000)
        self.tend_input.setToolTip(f"Choose a value between {min(lim1, lim2)} and {max(lim1, lim2)}")

        self.tstep_input = QDoubleSpinBox()
        lim1Step = 0.001
        lim2Step = 1000
        self.tstep_input.setRange(lim1Step, lim2Step)
        self.tstep_input.setValue(1)
        self.tstep_input.setSingleStep(1)
        self.tstep_input.setDecimals(3)
        self.tstep_input.setToolTip(f"Choose a value between {lim1Step} and {lim2Step}")

        #-------------------------------
        self.timeUnit_dropdown = QComboBox()
        self.timeUnit_dropdown.addItems([
            "yr",
            "kyr"
        ])
        self.timeUnit_dropdown.setCurrentIndex(1)
        self.timeUnit = self.timeUnit_dropdown.currentText()

        #-------------------------------
        form_layout.addRow("Type :", self.plotType_dropdown)
        form_layout.addRow("Astronomical solution :", self.solutionAstro_dropdown)
        form_layout.addRow("Solar constant [W/m2] :", self.solar_constant_input)
        form_layout.addRow("Latitude [°] :", self.latitude_input)
        form_layout.addRow("True longitude #1 [°] :", self.trueLongitude1_input)
        form_layout.addRow("True longitude #2 [°] :", self.trueLongitude2_input)
        form_layout.addRow("Time direction :", self.timeConvention_dropdown)
        form_layout.addRow("Time unit:", self.timeUnit_dropdown)
        self.label_tstart = QLabel(f"Start [{self.timeUnit}] :")
        form_layout.addRow(self.label_tstart, self.tstart_input)
        self.label_tend = QLabel(f"End [{self.timeUnit}] :")
        form_layout.addRow(self.label_tend, self.tend_input)
        self.label_tstep = QLabel(f"Step [{self.timeUnit}] :")
        form_layout.addRow(self.label_tstep, self.tstep_input)

        #-------------------------------
        groupbox1.setLayout(form_layout)
        col1_layout.addWidget(groupbox1)

        #----------------------------------------------
        col2_layout = QVBoxLayout()

        self.ref_Berger1978 = 'Berger, A. (1978) Long-term variations of daily insolation and Quaternary climatic changes. Journal of the Atmospheric Sciences, 35, 2362-2367. https://doi.org/10.1175/1520-0469(1978)035&lt;2362:LTVODI&gt;2.0.CO;2'
        self.ref_Laskar1993 = 'Laskar, J., Joutel, F., & Boudin, F. (1993). Orbital, precessional, and insolation quantities for the Earth from -20 Myr to +10 Myr. Astronomy and Astrophysics, 270(1-2), 522-533. https://adsabs.harvard.edu/full/1993A%26A...270..522L/0000522.000.html'
        self.ref_Laskar2004 = 'Laskar, J., Robutel, P., Joutel, F., Gastineau, M., Correia, A. C., & Levrard, B. (2004). A long-term numerical solution for the insolation quantities of the Earth. Astronomy & Astrophysics, 428(1), 261-285. https://doi.org/10.1051/0004-6361:20041335'
        self.ref_Laskar2010 = 'Laskar, J., Fienga, A., Gastineau, M., Manche, H.: (2011). A new orbital solution for the long-term motion of the Earth. Astron. Astrophys., Volume 532, A89. https://doi.org/10.48550/arXiv.1103.1084'

        self.ref = QLabel()
        self.ref.setText(f"Reference : <br><br>{self.ref_Laskar2004}")
        self.ref.setFixedWidth(400)
        self.ref.setWordWrap(True)
        self.ref.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.range_Laskar2010 = 'From -249999 to 0 kyears'
        self.range_Laskar2004 = 'From -101000 to 21000 kyears'
        self.range_Laskar1993 = 'From -20000 to 10000 kyears'
        self.range_Berger1978 = 'Unbounded'

        self.range = QLabel()
        self.range.setText(f"Range : <br><br>{self.range_Laskar2004}")
        self.range.setFixedWidth(400)
        self.range.setWordWrap(True)
        self.range.setTextInteractionFlags(Qt.TextSelectableByMouse)

        col2_layout.addWidget(self.ref)
        col2_layout.addSpacing(50)
        col2_layout.addWidget(self.range)
        col2_layout.addStretch()

        #----------------------------------------------
        col_layout.addLayout(col1_layout)
        col_layout.addLayout(col2_layout)
        col_layout.addStretch()
        main_layout.addLayout(col_layout)

        #----------------------------------------------
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.myplot)

        self.plotType_dropdown.currentIndexChanged.connect(self.plotType_change)
        self.solutionAstro_dropdown.currentIndexChanged.connect(self.solutionAstro_change)
        self.timeUnit_dropdown.currentIndexChanged.connect(self.timeUnit_change)
        self.timeConvention_dropdown.currentIndexChanged.connect(self.timeConvention_change)

        self.solar_constant_input.valueChanged.connect(self.delayed_update)
        self.latitude_input.valueChanged.connect(self.delayed_update)
        self.trueLongitude1_input.valueChanged.connect(self.delayed_update)
        self.trueLongitude2_input.valueChanged.connect(self.delayed_update)
        self.tstart_input.valueChanged.connect(self.delayed_update)
        self.tend_input.valueChanged.connect(self.delayed_update)
        self.tstep_input.valueChanged.connect(self.delayed_update)
        self.timeConvention_dropdown.currentIndexChanged.connect(self.delayed_update)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        self.import_button = QPushButton("Import serie", self)
        self.import_button.setStyleSheet("padding: 4px 12px;")
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

        self.plotType_change()
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def timeConvention_change(self):

        if self.timeConvention_dropdown.currentIndex() == 0:     # Past < 0
            self.t_convention = 1
        else:                                                    # Past > 0
            self.t_convention = -1

        lim1 = self.tstart_input.minimum() * (-1)
        lim2 = self.tstart_input.maximum() * (-1)
        value1 = self.tstart_input.value() * (-1) 
        value2 = self.tend_input.value() * (-1)

        self.tstart_input.blockSignals(True)
        self.tstart_input.setRange(min(lim1,lim2), max(lim1,lim2))
        self.tstart_input.setToolTip(f"Choose a value between {min(lim1,lim2)} and {max(lim1,lim2)}")
        self.tstart_input.setValue(min(value1, value2))
        self.tstart_input.blockSignals(False)

        self.tend_input.blockSignals(True)
        self.tend_input.setRange(min(lim1,lim2), max(lim1,lim2))
        self.tend_input.setToolTip(f"Choose a value between {min(lim1,lim2)} and {max(lim1,lim2)}")
        self.tend_input.setValue(max(value1, value2))
        self.tend_input.blockSignals(False)

        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def timeUnit_change(self):

        self.timeUnit = self.timeUnit_dropdown.currentText()
        self.label_tstart.setText(f"Start [{self.timeUnit}] :")
        self.label_tend.setText(f"End [{self.timeUnit}] :")
        self.label_tstep.setText(f"Step [{self.timeUnit}] :")

        lim1 = self.tstart_input.minimum()
        lim2 = self.tstart_input.maximum()
        value1 = self.tstart_input.value()
        value2 = self.tend_input.value()
        step_lim1 = self.tstep_input.minimum()
        step_lim2 = self.tstep_input.maximum()
        step_value = self.tstep_input.value()

        if self.timeUnit == 'yr':
            lim1 = lim1 * 1000
            lim2 = lim2 * 1000
            value1 = value1 * 1000
            value2 = value2 * 1000
            step = 1000
            step_lim1 = step_lim1 * 1000
            step_lim2 = step_lim2 * 1000
            step_value = step_value * 1000
        else:
            lim1 = lim1 // 1000
            lim2 = lim2 // 1000
            value1 = value1 // 1000
            value2 = value2 // 1000
            step = 1
            step_lim1 = step_lim1 / 1000
            step_lim2 = step_lim2 / 1000
            step_value = step_value / 1000

        self.tstart_input.blockSignals(True)
        self.tstart_input.setRange(lim1, lim2)
        self.tstart_input.setToolTip(f"Choose a value between {lim1} and {lim2}")
        self.tstart_input.setValue(value1)
        self.tstart_input.setSingleStep(step)
        self.tstart_input.blockSignals(False)

        self.tend_input.blockSignals(True)
        self.tend_input.setRange(lim1, lim2)
        self.tend_input.setToolTip(f"Choose a value between {lim1} and {lim2}")
        self.tend_input.setValue(value2)
        self.tend_input.setSingleStep(step)
        self.tend_input.blockSignals(False)

        self.tstep_input.blockSignals(True)
        self.tstep_input.setRange(step_lim1, step_lim2)
        self.tstep_input.setToolTip(f"Choose a value between {step_lim1} and {step_lim2}")
        self.tstep_input.setValue(step_value)
        self.tstep_input.setSingleStep(step)
        self.tstep_input.blockSignals(False)

        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def updateTrueLongitude2Limit(self, value):
        self.trueLongitude2_input.setMinimum(value + 1)

    #---------------------------------------------------------------------------------------------
    def plotType_change(self):

        self.plotType = self.plotType_dropdown.currentText()

        if self.plotType in ["Eccentricity", "Obliquity", "Precession angle", "Precession parameter"]:
            self.solar_constant_input.setEnabled(False)
            self.latitude_input.setEnabled(False)
            self.trueLongitude1_input.setEnabled(False)
            self.trueLongitude2_input.setEnabled(False)
        if self.plotType == "Daily insolation":
            self.solar_constant_input.setEnabled(True)
            self.latitude_input.setEnabled(True)
            self.trueLongitude1_input.setEnabled(True)
            self.trueLongitude2_input.setEnabled(False)
        elif self.plotType == "Integrated insolation between 2 true longitudes":
            self.solar_constant_input.setEnabled(True)
            self.latitude_input.setEnabled(True)
            self.trueLongitude1_input.setEnabled(True)
            self.trueLongitude2_input.setEnabled(True)
        elif self.plotType in ["Caloric summer insolation", "Caloric winter insolation"]:
            self.solar_constant_input.setEnabled(True)
            self.latitude_input.setEnabled(True)
            self.trueLongitude1_input.setEnabled(False)
            self.trueLongitude2_input.setEnabled(False)

        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def solutionAstro_change(self):

        def reinit_plotType_dropdow():
            for i in range(self.plotType_dropdown.count()):
                self.plotType_dropdown.setItemData(i, Qt.ItemIsEnabled | Qt.ItemIsSelectable, Qt.UserRole - 1)

        self.solutionAstro = self.solutionAstro_dropdown.currentText()

        if self.timeUnit == 'yr':
            scaleFactor = 1000
        else:
            scaleFactor = 1

        if self.solutionAstro.startswith("Laskar2010"):
            for i in range(self.plotType_dropdown.count()):
                if self.plotType_dropdown.itemText(i) != "Eccentricity":
                    self.plotType_dropdown.model().item(i).setFlags(Qt.NoItemFlags)
                else:
                    self.plotType_dropdown.model().item(i).setFlags(Qt.ItemIsEnabled)
            self.plotType_dropdown.setCurrentText("Eccentricity")
            lim1 = -249999
            lim2 = 0
            refText = self.ref_Laskar2010
            rangeText = self.range_Laskar2010

        elif self.solutionAstro.startswith("Laskar2004"):
            reinit_plotType_dropdow()
            lim1 = -101000
            lim2 = 21000 
            refText = self.ref_Laskar2004
            rangeText = self.range_Laskar2004

        elif self.solutionAstro.startswith("Laskar1993"):
            reinit_plotType_dropdow()
            lim1 = -20000
            lim2 = 10000 
            refText = self.ref_Laskar1993
            rangeText = self.range_Laskar1993

        else:
            reinit_plotType_dropdow()
            lim1 = -5E6
            lim2 = 5E6
            refText = self.ref_Berger1978
            rangeText = self.range_Berger1978

        lim1 = lim1 * self.t_convention * scaleFactor
        lim2 = lim2 * self.t_convention * scaleFactor
        self.tstart_input.setRange(int(min(lim1, lim2)), int(max(lim1, lim2)))
        self.tend_input.setRange(int(min(lim1, lim2)), int(max(lim1, lim2)))
        self.tstart_input.setToolTip(f"Choose a value between {min(lim1, lim2)} and {max(lim1, lim2)}")
        self.tend_input.setToolTip(f"Choose a value between {min(lim1, lim2)} and {max(lim1, lim2)}")
        self.ref.setText(f"Reference : <br><br>{refText}")
        self.range.setText(f"Range : <br><br>{rangeText}")
    
        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def delayed_update(self):
        self.status_bar.showMessage('Waiting', 1000)
        self.update_timer.start(1000)

    #---------------------------------------------------------------------------------------------
    def myplot(self):

        self.plotType = self.plotType_dropdown.currentText()
        self.solutionAstro = self.solutionAstro_dropdown.currentText()

        solar_constant = self.solar_constant_input.value()
        latitude = self.latitude_input.value()
        trueLongitude1 = self.trueLongitude1_input.value()
        trueLongitude2 = self.trueLongitude2_input.value()
        t_start = self.tstart_input.value()
        t_end = self.tend_input.value()
        t_step = self.tstep_input.value()

        t = np.arange(t_start, t_end + t_step, t_step) * self.t_convention

        if self.timeUnit == 'yr': t = t/1000

        deg_to_rad = np.pi/180.
       
        astro_params = eval(f"astro.Astro{self.solutionAstro}()")

        values = np.empty(len(t))

        piDeg = np.pi/180

        if self.plotType == "Eccentricity":
            ecc = astro_params.eccentricity(t)
            values = ecc / piDeg
            ylabel = "Eccentricity [degrees]"

        elif self.plotType == "Obliquity":
            obl = astro_params.obliquity(t)
            values = obl / piDeg
            ylabel = "Obliquity [degrees]"

        elif self.plotType == "Precession angle":
            pre = astro_params.precession_angle(t)
            values = pre / piDeg
            ylabel = "Precession angle [degrees]"

        elif self.plotType == "Precession parameter":
            preParam = astro_params.precession_parameter(t)
            values = preParam / piDeg
            ylabel = "Precession parameter [degrees]"

        elif self.plotType == "Daily insolation":
            ecc = astro_params.eccentricity(t)
            obl = astro_params.obliquity(t)
            pre = astro_params.precession_angle(t)
            for i in range(len(t)): 
                values[i] = solar_constant * \
                            inso.inso_dayly_radians(
                                    trueLongitude1*deg_to_rad,
                                    latitude*deg_to_rad, 
                                    obl[i], 
                                    ecc[i], 
                                    pre[i])
            ylabel = "Insolation [W/m2]"

        elif self.plotType == "Integrated insolation between 2 true longitudes":
            ecc = astro_params.eccentricity(t)
            obl = astro_params.obliquity(t)
            pre = astro_params.precession_angle(t)
            for i in range(len(t)): 
                values[i] = solar_constant * \
                            inso.inso_mean_radians(
                                    trueLongitude1*deg_to_rad,
                                    trueLongitude2*deg_to_rad,
                                    latitude*deg_to_rad, 
                                    obl[i], 
                                    ecc[i], 
                                    pre[i])
            ylabel = "Insolation [W/m2]"

        elif self.plotType == "Caloric summer insolation":
            ecc = astro_params.eccentricity(t)
            obl = astro_params.obliquity(t)
            pre = astro_params.precession_angle(t)
            for i in range(len(t)): 
                values[i] = solar_constant * \
                            inso.inso_caloric_summer_NH(
                                                    latitude*deg_to_rad, 
                                                    obl[i], 
                                                    ecc[i], 
                                                    pre[i])
            ylabel = "Insolation [W/m2]"

        elif self.plotType == "Caloric winter insolation":
            ecc = astro_params.eccentricity(t)
            obl = astro_params.obliquity(t)
            pre = astro_params.precession_angle(t)
            for i in range(len(t)): 
                values[i] = solar_constant * \
                            inso.inso_caloric_winter_NH(
                                                    latitude*deg_to_rad, 
                                                    obl[i], 
                                                    ecc[i], 
                                                    pre[i])
            ylabel = "Insolation [W/m2]"

        if self.timeUnit == 'yr':
            self.index = t * self.t_convention * 1000
        else:
            self.index = t * self.t_convention
        self.values = values

        ax = self.interactive_plot.axs[0]
        ax.clear()
        self.interactive_plot.reset()

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)

        color = "darkorange"
        line1, = ax.plot(self.index, self.values, linewidth=0.5, color=color)
        points1 = ax.scatter(self.index, self.values, s=5, marker='o', color=color, visible=False)
        ax.line_points_pairs.append((line1, points1))

        ax.set_xlabel(self.timeUnit)
        ax.set_ylabel(ylabel)
        ax.autoscale()

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()
        self.status_bar.showMessage('Updated', 1000)

    #---------------------------------------------------------------------------------------------
    def import_serie(self):

        if self.plotType in ["Eccentricity", "Obliquity", "Precession angle"]:
            history = f'Astronomical serie "{self.plotType}"' 
            shortName = f"{self.plotType} [degrees]"
            
        elif self.plotType == "Daily insolation":
            history = f'Insolation serie "{self.plotType}" with parameters :' + \
                        '<ul>' + \
                        f'<li>Solar constant [W/m2]: {self.solar_constant_input.value()}' + \
                        f'<li>Latitude [°]: {self.latitude_input.value()}' + \
                        f'<li>True longitude [°]: {self.trueLongitude1_input.value()}' + \
                        '</ul>'
            shortName = "Daily insolation [W/m2]"

        elif self.plotType == "Integrated insolation between 2 true longitudes":
            history = f'Insolation serie "{self.plotType}" with parameters :' + \
                        '<ul>' + \
                        f'<li>Solar constant [W/m2]: {self.solar_constant_input.value()}' + \
                        f'<li>Latitude [°]: {self.latitude_input.value()}' + \
                        f'<li>True longitude #1 [°]: {self.trueLongitude1_input.value()}' + \
                        f'<li>True longitude #2 [°]: {self.trueLongitude2_input.value()}' + \
                        '</ul>'
            shortName = "Integrated insolation [W/m2]"

        elif self.plotType == "Caloric summer insolation" or \
             self.plotType == "Caloric winter insolation":
            history = f'Insolation serie "{self.plotType}" with parameters :' + \
                        '<ul>' + \
                        f'<li>Solar constant [W/m2]: {self.solar_constant_input.value()}' + \
                        f'<li>Latitude [°]: {self.latitude_input.value()}' + \
                        '</ul>'
            shortName = f"{self.plotType} [W/m2]"

        serieDict = {
            'Id': generate_Id(), 
            'Type': 'Serie', 
            'Name': '', 
            'X': 'years',
            'Y': shortName,
            'Y axis inverted': False,
            'Color': generate_color(),
            'History': '<BR>' + history,
            'Comment': '',
            'Serie': pd.Series(self.values, index=self.index),
            }

        self.add_item_tree_widget(None, serieDict)          # will be added on parent from current index

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.open_insolationAstroSerieWindow.pop('123456', None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(parent, item):
        print('handle', parent, item)

    app = QApplication([])

    Id_insolationAstroSerieWindow = '1234'
    open_insolationAstroSerieWindow = {}

    insolationAstroSerieWindow = defineInsolationAstroSerieWindow(open_insolationAstroSerieWindow, handle_item)
    open_insolationAstroSerieWindow[Id_insolationAstroSerieWindow] = defineInsolationAstroSerieWindow
    insolationAstroSerieWindow.show()

    sys.exit(app.exec_())

