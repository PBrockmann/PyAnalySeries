from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.lines import Line2D

from .interactivePlot import interactivePlot

#=========================================================================================
import matplotlib
matplotlib.use("Qt5Agg")

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class displayTogetherSeriesWindow(QWidget):
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

        title = 'Display together series : ' + ', '.join(self.Ids)
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        #----------------------------------------------
        self.interactive_plot = interactivePlot()
        self.myplot()
        
        main_layout = QVBoxLayout()

        self.canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(self.canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        label_axis = QLabel("Separated axis :")
        self.combo_axis = QComboBox()
        self.combo_axis.addItems(["vertical", "horizontal", "none"])
        self.combo_axis.setCurrentText("none")

        self.close_button = QPushButton("Close", self)

        button_layout.addStretch()
        button_layout.addWidget(label_axis)
        button_layout.addWidget(self.combo_axis)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.close_button.clicked.connect(self.close)
        self.combo_axis.currentIndexChanged.connect(self.combo_axis_change)

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
    def combo_axis_change(self):
       
        for ax in self.interactive_plot.axs[:]:
            ax.clear()
            if ((hasattr(ax, "spine_left_position") and ax.spine_left_position != 0) or
                (hasattr(ax, "spine_bottom_position") and ax.spine_bottom_position != 0)):
                ax.remove()
                self.interactive_plot.axs.remove(ax)

        type = self.combo_axis.currentText()
        if type == 'vertical':
            self.myplot_separatedVerticalAxis()
        elif type == 'horizontal':
            self.myplot_separatedHorizontalAxis()
        else:
            self.myplot()

    #---------------------------------------------------------------------------------------------
    def myplot(self):

        self.interactive_plot.left_margin = 100 
        self.interactive_plot.bottom_margin = 50 

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

        ax.yaxis.set_inverted(any(Y_axisInverted_list))

        self.interactive_plot.on_resize(None)
        ax.figure.canvas.draw()
        ax.figure.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def myplot_separatedVerticalAxis(self):

        fig_width, fig_height = self.interactive_plot.fig.canvas.get_width_height()

        offset = 80
        self.interactive_plot.left_margin = len(self.items) * offset 
        self.interactive_plot.bottom_margin = 50

        legendHandles = []

        #---------------------------------
        item = self.items[0]
        serieDict = item.data(0, Qt.UserRole)
        serie = serieDict['Serie']
        serie = serie.groupby(serie.index).mean()
        serieColor = serieDict['Color']
        Y_axisInverted = serieDict['Y axis inverted']

        ax = self.interactive_plot.axs[0]
        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.autoscale()
        ax.patch.set_visible(False)
        ax.twins = []
        ax.twins_orientation = 'vertical'

        line, = ax.plot(serie.index, serie.values, color=serieColor, linewidth=self.serieWidth, label=serieDict['Y'])
        points = ax.scatter(serie.index, serie.values, s=5, marker='o', color=serieColor, visible=False)
        legendHandle = Line2D([0], [0], color=serieColor, label=serieDict['Y'])
        legendHandles.append(legendHandle)
        ax.line_points_pairs.append((line, points))
        ax.set_xlabel(self.xName)
        ax.set_ylabel(serieDict['Y'])
        ax.yaxis.label.set_color(serieColor)
        ax.yaxis.set_inverted(Y_axisInverted)

        #---------------------------------
        for n,item in enumerate(self.items[1:]):
            serieDict = item.data(0, Qt.UserRole)
            serie = serieDict['Serie']
            serie = serie.groupby(serie.index).mean()
            serieColor = serieDict['Color']
            Y_axisInverted = serieDict['Y axis inverted']

            twin = self.interactive_plot.axs[0].twinx()
            twin.spine_left_position = -offset * (n+1)
            twin.yaxis.set_label_position('left')
            twin.yaxis.set_ticks_position('left')
            twin.spines['right'].set_visible(False)
            twin.spines['top'].set_visible(False)
            twin.spines['bottom'].set_visible(False)
            twin.set_zorder(-10)

            line, = twin.plot(serie.index, serie.values, color=serieColor, linewidth=self.serieWidth, label=serieDict['Y'])
            points = twin.scatter(serie.index, serie.values, s=5, marker='o', color=serieColor, visible=False)
            legendHandle = Line2D([0], [0], color=serieColor, label=serieDict['Y'])
            legendHandles.append(legendHandle)
            twin.set(ylabel=serieDict['Y'])
            twin.yaxis.label.set_color(serieColor)
            twin.yaxis.set_inverted(Y_axisInverted)
            twin.line_points_pairs = []
            twin.line_points_pairs.append((line, points))
            self.interactive_plot.axs.append(twin)

            ax.twins.append(twin)

        #---------------------------------
        legend = ax.legend(handles=legendHandles)

        for n,axcurrent in enumerate(self.interactive_plot.axs):
            legend_line = legend.get_lines()[n]
            axcurrent_line = axcurrent.get_lines()[0]
            legend_line.set_picker(5)
            ax.map_legend_to_line[legend_line] = axcurrent_line

        #---------------------------------
        self.interactive_plot.on_resize(None)
        ax.figure.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def myplot_separatedHorizontalAxis(self):

        fig_width, fig_height = self.interactive_plot.fig.canvas.get_width_height()

        offset = 80
        self.interactive_plot.left_margin = 100
        self.interactive_plot.bottom_margin = len(self.items) * offset 

        legendHandles = []

        #---------------------------------
        item = self.items[0]
        serieDict = item.data(0, Qt.UserRole)
        serie = serieDict['Serie']
        serie = serie.groupby(serie.index).mean()
        serieColor = serieDict['Color']
        Y_axisInverted = serieDict['Y axis inverted']

        ax = self.interactive_plot.axs[0]
        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.autoscale()
        Y_axisInverted_list = []
        ax.patch.set_visible(False)
        ax.twins = []
        ax.twins_orientation = 'horizontal'

        line, = ax.plot(serie.index, serie.values, color=serieColor, linewidth=self.serieWidth, label=serieDict['Y'])
        points = ax.scatter(serie.index, serie.values, s=5, marker='o', color=serieColor, visible=False)
        legendHandle = Line2D([0], [0], color=serieColor, label=serieDict['Y'])
        legendHandles.append(legendHandle)
        ax.line_points_pairs.append((line, points))
        ax.set_xlabel(self.xName)
        ax.set_ylabel('')
        ax.xaxis.label.set_color(serieColor)
        ax.yaxis.set_inverted(Y_axisInverted)

        #---------------------------------
        for n,item in enumerate(self.items[1:]):
            serieDict = item.data(0, Qt.UserRole)
            serie = serieDict['Serie']
            serie = serie.groupby(serie.index).mean()
            serieColor = serieDict['Color']
            Y_axisInverted_list.append(serieDict['Y axis inverted'])

            twin = self.interactive_plot.axs[0].twiny()
            twin.spine_bottom_position = -offset * (n+1)
            twin.xaxis.set_label_position('bottom')
            twin.xaxis.set_ticks_position('bottom')
            twin.spines['left'].set_visible(False)
            twin.spines['right'].set_visible(False)
            twin.spines['top'].set_visible(False)
            twin.set_zorder(-10)

            line, = twin.plot(serie.index, serie.values, color=serieColor, linewidth=self.serieWidth, label=serieDict['Y'])
            points = twin.scatter(serie.index, serie.values, s=5, marker='o', color=serieColor, visible=False)
            legendHandle = Line2D([0], [0], color=serieColor, label=serieDict['Y'])
            legendHandles.append(legendHandle)
            twin.set(xlabel=serieDict['X'])
            twin.xaxis.label.set_color(serieColor)
            twin.yaxis.set_inverted(Y_axisInverted)
            twin.line_points_pairs = []
            twin.line_points_pairs.append((line, points))
            self.interactive_plot.axs.append(twin)

            ax.twins.append(twin)

        #---------------------------------
        legend = ax.legend(handles=legendHandles)

        for n,axcurrent in enumerate(self.interactive_plot.axs):
            legend_line = legend.get_lines()[n]
            axcurrent_line = axcurrent.get_lines()[0]
            legend_line.set_picker(5)
            ax.map_legend_to_line[legend_line] = axcurrent_line

        ax.yaxis.set_inverted(any(Y_axisInverted_list))

        #---------------------------------
        self.interactive_plot.on_resize(None)
        ax.figure.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def sync_with_item(self, item):
        if not item in self.items: return

        self.raise_()
        self.combo_axis_change()

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
    displayWindow = displayTogetherSeriesWindow(Id_displayWindow, open_displayWindows, [item1, item2])
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app.exec_())
