from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from .CustomQTableWidget import CustomQTableWidget 
from .interactivePlot import interactivePlot
from .defineInterpolationWindow import defineInterpolationWindow

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class displaySingleSerieWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_displayWindows, item):
        super().__init__()

        self.Id = Id
        self.open_displayWindows = open_displayWindows
        self.item = item

        self.serieWidth = 0.8

        self.serieDict = self.item.data(0, Qt.UserRole)
        self.Y_axisInverted = self.serieDict['Y axis inverted']

        self.xName = self.serieDict['X']
        self.yName = self.serieDict['Y']
        serie = self.serieDict['Serie']

        title = 'Display serie : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        self.tabs = QTabWidget()
        
        #----------------------------------------------
        data_tab = QWidget()
        data_layout = QVBoxLayout()
        data_table = CustomQTableWidget()
        data_table.setRowCount(len(serie))
        data_table.setColumnCount(2)
        data_table.setHorizontalHeaderLabels([self.xName, self.yName])
        duplicates = serie.index.duplicated()
        missing_values = serie.isna().to_numpy()
        for i in range(len(serie)):
            data_table.setItem(i, 0, QTableWidgetItem(str(f'{serie.index[i]:.6f}')))
            data_table.setItem(i, 1, QTableWidgetItem(str(f'{serie.values[i]:.6f}')))
            if duplicates[i]:
                background_color = QColor('lemonchiffon')
            elif missing_values[i]:
                background_color = QColor('peachpuff')
            else:
                background_color = QColor('whitesmoke') if i % 2 == 0 else QColor('white')
            data_table.item(i, 0).setBackground(background_color)
            data_table.item(i, 1).setBackground(background_color)
        data_table.resizeColumnsToContents()

        data_layout.addWidget(data_table)
        data_tab.setLayout(data_layout)
        
        #----------------------------------------------
        stats_tab = QWidget()
        stats_layout = QVBoxLayout()
        stats_table = CustomQTableWidget()
        stats_table.setRowCount(6)
        stats_table.setColumnCount(2)
        stats_table.setHorizontalHeaderLabels(["Stat", "Value"])
        stats = {
            "Number of points": (len(serie), 'd'),
            "Number of duplicates": ((serie.index.value_counts() > 1).sum(), 'd'),
            "Number of missing": (serie.isna().sum(), 'd'),
            "Mean": (serie.mean(), '.2f'),
            "Maximum": (serie.max(), '.2f'),
            "Minimum": (serie.min(), '.2f'),
        }
        for i, (key, value) in enumerate(stats.items()):
            stats_table.setItem(i, 0, QTableWidgetItem(key))
            stats_table.setItem(i, 1, QTableWidgetItem(f"{value[0]:{value[1]}}"))
            if i%2 == 0:
                stats_table.item(i, 0).setBackground(QColor(250, 250, 250))
                stats_table.item(i, 1).setBackground(QColor(250, 250, 250))
        stats_table.resizeColumnsToContents()

        stats_layout.addWidget(stats_table)
        stats_tab.setLayout(stats_layout)
        
        #----------------------------------------------
        plot_tab = QWidget()
        plot_layout = QVBoxLayout()
   
        self.interactive_plot = interactivePlot()
        canvas = FigureCanvas(self.interactive_plot.fig)
        plot_layout.addWidget(canvas)
        self.myplot()
        
        plot_tab.setLayout(plot_layout)

        #----------------------------------------------
        info_tab = QWidget()
        info_layout = QVBoxLayout()

        self.textName = QLabel(f"Name : <b>{self.serieDict['Name']}</b>")

        labelHistory = QLabel("History :")
        self.textHistory = QTextEdit()
        self.textHistory.setFixedHeight(self.textHistory.fontMetrics().lineSpacing() * 10)
        self.textHistory.setText(self.serieDict['History'])
        self.textHistory.setReadOnly(True)
        self.textHistory.setStyleSheet("""
            QTextEdit[readOnly="true"] {
                background-color: #f8f8f8;
                border: 1px solid lightgray;
                font-family: Courier New;
                font-size: 12;
            }
        """)

        labelComment = QLabel("Comment :")
        self.textComment = QTextEdit()
        self.textComment.setFixedHeight(self.textComment.fontMetrics().lineSpacing() * 10)
        self.textComment.setText(self.serieDict['Comment'])

        info_layout.addWidget(self.textName)
        info_layout.addWidget(labelHistory)
        info_layout.addWidget(self.textHistory)
        info_layout.addWidget(labelComment)
        info_layout.addWidget(self.textComment)
        info_layout.addStretch()

        info_tab.setLayout(info_layout)

        #----------------------------------------------
        self.tabs.addTab(data_tab, "Data")
        self.tabs.addTab(stats_tab, "Stats")
        self.tabs.addTab(plot_tab, "Plot")
        self.tabs.addTab(info_tab, "Info")
        self.tabs.setCurrentIndex(2)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        self.close_button = QPushButton("Close", self)
        button_layout.addStretch()

        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.close_button.clicked.connect(self.close)

        #----------------------------------------------
        self.setLayout(main_layout)

        menu_bar = QMenuBar(self)
        main_layout.setMenuBar(menu_bar)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

    #---------------------------------------------------------------------------------------------

        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def contextMenuEvent(self, event):
        current_tab_index = self.tabs.currentIndex()
        if current_tab_index == 2:                  # Plot
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

        self.interactive_plot.left_margin = 100

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)
        ax.autoscale()
        serieDict = self.item.data(0, Qt.UserRole)
        serie = serieDict['Serie']
        serie = serie.groupby(serie.index).mean()
        serieColor = serieDict['Color']
        Y_axisInverted = serieDict['Y axis inverted']

        line, = ax.plot(serie.index, serie.values, color=serieColor, linewidth=self.serieWidth)
        points = ax.scatter(serie.index, serie.values, s=5, marker='o', color=serieColor, visible=False)
        ax.line_points_pairs.append((line, points))

        if 'InterpolationMode' in serieDict:
            interpolationMode = serieDict['InterpolationMode']
            XOriginal = serieDict['XOriginal']
            X1Coords = serieDict['X1Coords']
            X2Coords = serieDict['X2Coords']
            (f_1to2, f_2to1) = defineInterpolationWindow.defineInterpolationFunctions(X1Coords, X2Coords, interpolationMode=interpolationMode)

            second_xaxis = ax.secondary_xaxis('top', functions=(f_1to2, f_2to1))
            second_xaxis.tick_params(labelrotation=30)
            second_xaxis.set_xlabel(XOriginal)
            plt.setp(second_xaxis.get_xticklabels(), horizontalalignment='left')

            self.interactive_plot.top_margin = 100

        if limits:
            ax.set_xlim(limits[0])
            ax.set_ylim(limits[1])
        ax.yaxis.set_inverted(Y_axisInverted)

        ax.figure.canvas.draw()
        ax.figure.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def sync_with_item(self, item):
        if item != self.item: return

        self.raise_()

        self.serieDict = self.item.data(0, Qt.UserRole)
        self.textName.setText(f"Name : <b>{self.serieDict['Name']}</b>")
        xlim = self.interactive_plot.axs[0].get_xlim()
        ylim = self.interactive_plot.axs[0].get_ylim()
        self.interactive_plot.axs[0].clear()
        self.myplot(limits=[xlim,ylim])

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.serieDict['Comment'] = self.textComment.toPlainText()
        self.item.setData(0, Qt.UserRole, self.serieDict)
        self.open_displayWindows.pop(self.Id, None)
        event.accept()

#=========================================================================================

# Example usage
if __name__ == "__main__":

    app = QApplication(sys.argv)

    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    serie = pd.Series(y, index=x)

    itemDict = {
        'Id': 'abcd',
        'Name': 'A name',
        'X': 'xName',
        'Y': 'yName',
        'Serie': serie, 
        'Color': 'darkorange',
        'Y axis inverted': True,
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }

    item = QTreeWidgetItem()
    item.setData(0, Qt.UserRole, itemDict)

    open_displayWindows = {}
    Id_displayWindow = '1234'
    displayWindow = displaySingleSerieWindow(Id_displayWindow, open_displayWindows, item)
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app.exec_())
