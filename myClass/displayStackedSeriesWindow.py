from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .interactivePlot import interactivePlot

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class displayStackedSeriesWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Ids, open_displayWindows, items):
        super().__init__()

        self.Ids = Ids
        self.open_displayWindows = open_displayWindows
        self.items = items 

        self.serieWidth = 0.8

        title = 'Display stacked series : ' + ', '.join(self.Ids)
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1000, 800)
        self.setMinimumSize(800, 600)
        
        #----------------------------------------------
        self.interactive_plot = interactivePlot(rows=len(items), cols=1)
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
        exit_shortcut = QShortcut(QKeySequence('Q'), self)
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
    def myplot(self):

        #-----------------------------------
        for n, item in enumerate(self.items):

            ax = self.interactive_plot.axs[n]

            serieDict = item.data(0, Qt.UserRole)

            ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
            ax.set_xlabel(serieDict['X'])
            ax.set_ylabel(serieDict['Y'])
            ax.autoscale()

            serie = serieDict['Serie']
            serie = serie.groupby(serie.index).mean()
            serieColor = serieDict['Color']
            Y_axisInverted = serieDict['Y axis inverted']

            ax.line_points_pairs = []
            line, = ax.plot(serie.index, serie.values, color=serieColor, linewidth=self.serieWidth)
            points = ax.scatter(serie.index, serie.values, s=5, marker='o', color=serieColor, visible=False)
            ax.line_points_pairs.append((line, points))

            ax.yaxis.set_inverted(Y_axisInverted)

        #-----------------------------------
        XDict = {}
        for n, item in enumerate(self.items):
            serieDict = item.data(0, Qt.UserRole)
            if serieDict['X'] not in XDict:
                XDict[serieDict['X']] = []
            XDict[serieDict['X']].append(n)

        sharexLists = [n for n in XDict.values() if len(n) > 1]
        #print(sharexLists)
        for sharexList in sharexLists:
            for n in sharexList[1:]:
                #print("sharex", sharexList[0], n)
                self.interactive_plot.axs[sharexList[0]].sharex(self.interactive_plot.axs[n])

        #-----------------------------------
        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def sync_with_item(self, item):
        if not item in self.items: return

        self.raise_()

        for ax in self.interactive_plot.axs:
            ax.clear()
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
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
    y2 = np.cos(x2)
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
    displayWindow = displayStackedSeriesWindow(Id_displayWindow, open_displayWindows, [item1, item2])
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app.exec_())
