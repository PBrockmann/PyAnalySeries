from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from .misc import *
from .interactivePlot import interactivePlot

import sys
import numpy as np
import pandas as pd

from scipy import interpolate

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineSampleWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_sampleWindows, item, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_sampleWindows = open_sampleWindows
        self.item = item
        self.add_item_tree_widget = add_item_tree_widget

        self.serieWidth = 0.8
        self.step = 5
        self.kind = 'linear' 

        title = 'Define SAMPLE : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters')
        groupbox1_layout = QVBoxLayout()
        groupbox1.setFixedHeight(150)

        layout_s1 = QHBoxLayout()
        label_s1 = QLabel('Sampling step :')
        self.step_spinbox = QDoubleSpinBox(self)
        self.step_spinbox.setRange(0.5, 100)
        self.step_spinbox.setSingleStep(.5)
        self.step_spinbox.setValue(2)
        self.step_spinbox.setDecimals(2)
        self.step_spinbox.setFixedWidth(80)
        self.step_spinbox.valueChanged.connect(self.update_value)
        layout_s1.addWidget(label_s1)
        layout_s1.addWidget(self.step_spinbox)
        layout_s1.addStretch()

        layout_s2 = QHBoxLayout()
        label_s2 = QLabel('Kind of interpolation :')
        self.kind_dropdown = QComboBox()
        self.kind_dropdown.addItems([
             'nearest', 'zero', 'linear', 'quadratic', 'cubic'
        ])
        self.kind_dropdown.setFixedWidth(100)
        self.kind_dropdown.setCurrentText(self.kind)
        self.kind_dropdown.currentIndexChanged.connect(self.update_value)
        layout_s2.addWidget(label_s2)
        layout_s2.addWidget(self.kind_dropdown)
        layout_s2.addStretch()

        groupbox1_layout.addLayout(layout_s1)
        groupbox1_layout.addLayout(layout_s2)
        groupbox1_layout.addStretch()

        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()
        self.myplot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save sample and serie sampled", self)
        self.close_button = QPushButton("Close", self)
        button_layout.addStretch()

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.save_serie)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        self.interactive_plot.fig.canvas.setFocus()

        #self.status_bar.showMessage('Ready', 5000)

    #---------------------------------------------------------------------------------------------
    def update_value(self):

        self.step = self.step_spinbox.value()
        self.kind = self.kind_dropdown.currentText()
        print(self.step, self.kind)
        self.interactive_plot.axs[0].clear()
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def myplot(self, limits=None):

        self.serieDict = self.item.data(0, Qt.UserRole)
        self.xName = self.serieDict['X']
        self.yName = self.serieDict['Y']
        self.serie = self.serieDict['Serie']
        self.serie = self.serie.groupby(self.serie.index).mean()

        ax = self.interactive_plot.axs[0]

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)
        ax.autoscale()

        serieSampled = self.sample(self.serie, self.step, self.kind)
        serieColor = self.serieDict['Color']
        Y_axisInverted = self.serieDict['Y axis inverted']
        ax.yaxis.set_inverted(Y_axisInverted)

        line1, = ax.plot(self.serie.index, self.serie.values, color=serieColor, linewidth=self.serieWidth, label='Original')
        points1 = ax.scatter(self.serie.index, self.serie.values, s=5, marker='o', color=serieColor, visible=False)
        ax.line_points_pairs.append((line1, points1))
        
        line2, = ax.plot(serieSampled.index, serieSampled.values, color='black', linewidth=self.serieWidth, alpha=0.4, label='Sampled')
        points2 = ax.scatter(serieSampled.index, serieSampled.values, s=5, marker='o', color='black', alpha=0.4, visible=False)
        ax.line_points_pairs.append((line2, points2))

        legend = ax.legend()
        for legend_line, ax_line in zip(legend.get_lines(), ax.get_lines()):
            legend_line.set_picker(5)
            ax.map_legend_to_line[legend_line] = ax_line

        if limits:
            ax.set_xlim(limits[0])
            ax.set_ylim(limits[1])
            ax.yaxis.set_inverted(Y_axisInverted)

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def sync_with_item(self, item):
        if item != self.item: return

        self.raise_()

        xlim = self.interactive_plot.axs[0].get_xlim()
        ylim = self.interactive_plot.axs[0].get_ylim()
        self.interactive_plot.axs[0].clear()
        self.myplot(limits=[xlim,ylim])

    #---------------------------------------------------------------------------------------------
    @staticmethod
    def sample(serie, step, kind):

        index_min = serie.index.min()
        index_max = serie.index.max()

        index_min = np.ceil(index_min / step) * step
        index_max = np.floor(index_max / step) * step

        sampled_index = np.arange(index_min, index_max + 1E-9, step)
        sampled_index = np.sort(np.random.uniform(index_min, index_max, 10))
        print(sampled_index)

        interpolator = interpolate.interp1d(serie.index, serie.values, kind=kind, fill_value="extrapolate")
        sampled_values = interpolator(sampled_index)
        result_serie = pd.Series(sampled_values, index=sampled_index)

        return result_serie

    #---------------------------------------------------------------------------------------------
    def save_serie(self):
        sample_Id = generate_Id()
        sampleDict = {
            'Id': sample_Id,
            'Type': 'SAMPLE', 
            'Name': f'Sample every {self.step}', 
            'Parameters': f'{self.step} ; {self.kind}',
            'Comment': '',
            'History': f'sample with parameters' + \
                    '<ul>' + \
                    f'<li>Step : {self.step}' + \
                    f'<li>Kind of interpolation : {self.kind}' + \
                    '</ul>'
        }
        self.add_item_tree_widget(self.item.parent(), sampleDict)

        sampled_Id = generate_Id()
        sampled_serieDict = self.serieDict | {'Id': sampled_Id, 
            'Type': 'Serie sampled', 
            'Name': f'Serie sampled every {self.step}', 
            'Serie': self.sample(self.serie, self.step, self.kind),
            'Color': generate_color(exclude_color=self.serieDict['Color']),
            'History': append_to_htmlText(self.serieDict['History'], 
                f'serie <i><b>{self.serieDict["Id"]}</i></b> sampled with SAMPLE <i><b>{sample_Id}</i></b><BR>every {self.step} using kind of interpolation {self.kind}<BR>---> serie <i><b>{sampled_Id}</b></i>'),
            'Comment': '',
        }
        position = self.item.parent().indexOfChild(self.item)
        self.add_item_tree_widget(self.item.parent(), sampled_serieDict, position+1)

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.open_sampleWindows.pop(self.Id, None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(parent, item):
        print('handle', parent, item)

    app = QApplication([])

    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    serie = pd.Series(y, index=x)

    serieDict = {'Id': 'abcd', 'X': 'xName', 'Y': 'yName', 'Serie': serie, 
            'Color': 'darkorange', "Y axis inverted": True, 
            'Comment': 'A text', 'History': 'command1 ; command2'}
    item = QTreeWidgetItem()
    item.setData(0, Qt.UserRole, serieDict)

    open_sampleWindows = {}
    Id_sampleWindow = '1234'
    sampleWindow = defineSampleWindow(Id_sampleWindow, open_sampleWindows, item, handle_item)
    open_sampleWindows[Id_sampleWindow] = sampleWindow
    sampleWindow.show()

    sys.exit(app.exec_())
