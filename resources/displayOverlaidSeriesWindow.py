from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .interactivePlot import interactivePlot

#=========================================================================================
import matplotlib
matplotlib.use("Qt5Agg")

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class displayOverlaidSeriesWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Ids, open_displayWindows, items):
        super().__init__()

        self.Ids = Ids
        self.open_displayWindows = open_displayWindows
        self.items = items 

        self.serieWidth = 0.8

        serieDict = self.items[0].data(0, Qt.UserRole)
        self.xName = serieDict['X']
        self.yName = serieDict['Y']
        serie = serieDict['Serie']

        title = 'Display overlaid series : ' + ', '.join(self.Ids)
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        #----------------------------------------------
        self.interactive_plot = interactivePlot()
        self.myplot()
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.interactive_plot.fig.canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        self.close_button = QPushButton("Close", self)
        button_layout.addStretch()

        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.close_button.clicked.connect(self.close)

        self.setLayout(main_layout)

        #----------------------------------------------
        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        print_action = QAction("Save plot as PNG or PDF", self)
        print_action.triggered.connect(self.savePlot)
        context_menu.addAction(print_action)
        context_menu.exec_(event.globalPos())

    #---------------------------------------------------------------------------------------------
    def savePlot(self):
        fileName, _ = QFileDialog.getSaveFileName(self, 'Save Plots', '', 'PNG Files (*.png);;PDF Files (*.pdf)')
        if fileName:
            plt.savefig(fileName)

    #---------------------------------------------------------------------------------------------
    def myplot(self, limits=None):

        ax = self.interactive_plot.axs[0]

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel('')
        ax.autoscale()
        Y_axisInverted_list = []
        for item in self.items:
            serieDict = item.data(0, Qt.UserRole)
            serie = serieDict['Serie']
            serie = serie.groupby(serie.index).mean()
            serieColor = serieDict['Color']
            Y_axisInverted_list.append(serieDict['Y axis inverted'])

            line, = ax.plot(serie.index, serie.values, color=serieColor, linewidth=self.serieWidth, label=serieDict['Y'])
            points = ax.scatter(serie.index, serie.values, s=5, marker='o', color=serieColor, visible=False)
            ax.line_points_pairs.append((line, points))

        legend = ax.legend()
        for legend_line, ax_line in zip(legend.get_lines(), ax.get_lines()):
            legend_line.set_picker(5)
            ax.map_legend_to_line[legend_line] = ax_line

        if limits:
            ax.set_xlim(limits[0])
            ax.set_ylim(limits[1])
        ax.yaxis.set_inverted(any(Y_axisInverted_list))

        ax.figure.canvas.draw()
        ax.figure.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def sync_with_item(self, item):
        if not item in self.items: return

        self.raise_()

        xlim = self.interactive_plot.axs[0].get_xlim()
        ylim = self.interactive_plot.axs[0].get_ylim()
        self.interactive_plot.axs[0].clear()
        self.myplot(limits=[xlim,ylim])

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.open_displayWindows.pop(self.Ids, None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    app = QApplication(sys.argv)

    x1 = np.linspace(0, 10, 100)
    y1 = np.sin(x1)
    serie1 = pd.Series(y1, index=x1)

    serie1Dict = {
        'Id': '111',
        'X': 'x1Name',
        'Y': 'y1Name',
        'Serie': serie1,
        'Color': 'steelblue',
        'Y axis inverted': True,
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }
    item1 = QTreeWidgetItem()
    item1.setData(0, Qt.UserRole, serie1Dict)

    x2 = np.linspace(5, 15, 100)
    y2 = np.cos(x2)*4
    serie2 = pd.Series(y2, index=x2)

    serie2Dict = {
        'Id': '222',
        'X': 'x2Name',
        'Y': 'y2Name',
        'Serie': serie2,
        'Color': 'darkorange',
        'Y axis inverted': True,
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }
    item2 = QTreeWidgetItem()
    item2.setData(0, Qt.UserRole, serie2Dict)

    open_displayWindows = {}
    Id_displayWindow = tuple([serie1Dict['Id'], serie2Dict['Id']])
    displayWindow = displayOverlaidSeriesWindow(Id_displayWindow, open_displayWindows, [item1, item2])
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app.exec_())
