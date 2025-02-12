from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

from .misc import *
from .interactivePlot import interactivePlot

import sys
import numpy as np
import pandas as pd

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineFilterWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_filterWindows, item, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_filterWindows = open_filterWindows
        self.item = item
        self.add_item_tree_widget = add_item_tree_widget

        self.serieWidth = 0.8
        self.window_size = 5

        title = 'Define FILTER : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters')
        groupbox1_layout = QVBoxLayout()
        groupbox1.setFixedHeight(150)

        layout_s1 = QHBoxLayout()

        label_s1 = QLabel('Moving average window size :')
        self.spin_box = QSpinBox(self)
        self.spin_box.setRange(1, 33)
        self.spin_box.setSingleStep(2)
        self.spin_box.setValue(5)
        self.spin_box.setFixedWidth(50)
        self.spin_box.valueChanged.connect(self.update_value)
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

        self.save_button = QPushButton("Save filter and serie filtered", self)
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
        self.window_size = self.spin_box.value()
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

        serieFiltered = self.moving_average(self.serie, window_size=self.window_size)
        serieColor = self.serieDict['Color']
        Y_axisInverted = self.serieDict['Y axis inverted']
        ax.yaxis.set_inverted(Y_axisInverted)

        line1, = ax.plot(self.serie.index, self.serie.values, color=serieColor, linewidth=self.serieWidth, label='Original')
        points1 = ax.scatter(self.serie.index, self.serie.values, s=5, marker='o', color=serieColor, visible=False)
        ax.line_points_pairs.append((line1, points1))
        
        line2, = ax.plot(serieFiltered.index, serieFiltered.values, color='black', linewidth=self.serieWidth, alpha=0.4, label='Filtered')
        points2 = ax.scatter(serieFiltered.index, serieFiltered.values, s=5, marker='o', color='black', alpha=0.4, visible=False)
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
    def moving_average(serie, window_size=5):
        if window_size == 1:
            result_serie = serie
        else:
            half_window = window_size // 2
            result_values = np.convolve(serie.values, np.ones(window_size), 'valid') / window_size
            adjusted_index = serie.index[half_window: -half_window]
            result_serie = pd.Series(result_values, index=adjusted_index)
        return result_serie

    #---------------------------------------------------------------------------------------------
    def save_serie(self):
        filter_Id = generate_Id()
        filterDict = {
            'Id': filter_Id,
            'Type': 'FILTER', 
            'Name': f'Moving average {self.window_size} pts', 
            'Parameters': f'{self.window_size}',
            'Comment': '',
            'History': f'filter as a moving average of size {self.window_size}',
        }
        self.add_item_tree_widget(self.item.parent(), filterDict)

        filtered_Id = generate_Id()
        filtered_serieDict = self.serieDict | {'Id': filtered_Id, 
            'Type': 'Serie filtered', 
            'Serie': self.moving_average(self.serie, self.window_size),
            'Color': generate_color(exclude_color=self.serieDict['Color']),
            'History': append_to_htmlText(self.serieDict['History'], 
                f'serie <i><b>{self.serieDict["Id"]}</i></b> filtered with FILTER <i><b>{filter_Id}</i></b> with a moving average of size {self.window_size}<BR>---> serie <i><b>{filtered_Id}</b></i>'),
            'Comment': '',
        }
        position = self.item.parent().indexOfChild(self.item)
        self.add_item_tree_widget(self.item.parent(), filtered_serieDict, position+1)

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.open_filterWindows.pop(self.Id, None)
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

    open_filterWindows = {}
    Id_filterWindow = '1234'
    filterWindow = defineFilterWindow(Id_filterWindow, open_filterWindows, item, handle_item)
    open_filterWindows[Id_filterWindow] = filterWindow
    filterWindow.show()

    sys.exit(app.exec_())
