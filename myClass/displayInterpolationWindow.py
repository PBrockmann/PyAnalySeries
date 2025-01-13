from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from .CustomQTableWidget import CustomQTableWidget 
from .interactivePlot import interactivePlot
from .defineInterpolationWindow import defineInterpolationWindow

#=========================================================================================
class displayInterpolationWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_displayWindows, item):
        super().__init__()

        self.Id = Id
        self.open_displayWindows = open_displayWindows
        self.item = item

        self.interpolationDict = self.item.data(0, Qt.UserRole)

        self.X1Coords = self.interpolationDict['X1Coords']
        self.X2Coords = self.interpolationDict['X2Coords']
        self.X1Name = self.interpolationDict['X1Name']

        title = 'Display INTERPOLATION : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 800, 300)
        
        self.tabs = QTabWidget()
       
        #----------------------------------------------
        pointers_tab = QWidget()
        pointers_layout = QVBoxLayout()
        pointers_table = CustomQTableWidget()
        pointers_table.setRowCount(len(self.X1Coords))
        pointers_table.setColumnCount(2)
        pointers_table.setHorizontalHeaderLabels([self.X1Name, 'X'])
        pointers_table.resizeColumnsToContents()
        for i in range(len(self.X1Coords)):
            pointers_table.setItem(i, 0, QTableWidgetItem(str(f'{self.X1Coords[i]:.6f}')))
            pointers_table.setItem(i, 1, QTableWidgetItem(str(f'{self.X2Coords[i]:.6f}')))
            background_color = QColor('whitesmoke') if i % 2 == 0 else QColor('white')
            pointers_table.item(i, 0).setBackground(background_color)
            pointers_table.item(i, 1).setBackground(background_color)
        pointers_table.resizeColumnsToContents()

        pointers_layout.addWidget(pointers_table)
        pointers_tab.setLayout(pointers_layout)

        #----------------------------------------------
        pointersPlot_tab = QWidget()
        pointersPlot_layout = QVBoxLayout()

        self.interactive_pointersPlot = interactivePlot()
        self.interactive_pointersPlot.right_margin = 100

        pointersPlot_ax = self.interactive_pointersPlot.axs[0]

        line, = pointersPlot_ax.plot(self.X2Coords, self.X1Coords, color='steelblue', linewidth=1, label='aaaa')
        points = pointersPlot_ax.scatter(self.X2Coords, self.X1Coords, s=10, marker='o', color='steelblue')

        pointersPlot_ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=1)
        pointersPlot_ax.set_xlabel(self.X1Name)
        pointersPlot_ax.set_ylabel('X')

        pointersPlot_axGradient = pointersPlot_ax.twinx()
        pointersPlot_axGradient.set_ylabel('Gradients', color='darkorange')

        X2CoordsValues = np.linspace(self.X2Coords[0], self.X2Coords[-1], 100)

        (f_1to2, f_2to1) = defineInterpolationWindow.defineInterpolationFunctions(self.X1Coords, self.X2Coords, interpolationMode='Linear')
        gradientLinear = np.gradient(f_2to1(X2CoordsValues), X2CoordsValues).astype(np.float32)      # to avoid unnecessary precision
        line1, = pointersPlot_axGradient.plot(X2CoordsValues, gradientLinear, color='darkorange', lw=1, label='Linear')

        (f_1to2, f_2to1) = defineInterpolationWindow.defineInterpolationFunctions(self.X1Coords, self.X2Coords, interpolationMode='PCHIP')
        gradientPCHIP = np.gradient(f_2to1(X2CoordsValues), X2CoordsValues).astype(np.float32)       # to avoid unnecessary precision
        line2, = pointersPlot_axGradient.plot(X2CoordsValues, gradientPCHIP, color='darkorange', linestyle='dashed', lw=1, label='PCHIP')

        lines = [line1, line2]
        labels = [line.get_label() for line in lines]
        pointersPlot_ax.legend(lines, labels)
        
        pointersPlot_axGradient.autoscale(axis='y', tight=False)

        pointersPlot_ax.patch.set_alpha(0)
        pointersPlot_axGradient.set_zorder(pointersPlot_ax.get_zorder() - 1)

        self.interactive_pointersPlot.fig.canvas.draw()

        pointersPlot_layout.addWidget(self.interactive_pointersPlot.fig.canvas)
        pointersPlot_tab.setLayout(pointersPlot_layout)

        #----------------------------------------------
        info_tab = QWidget()
        info_layout = QVBoxLayout()

        self.textName = QLabel(f"Name : <b>{self.interpolationDict['Name']}</b>")

        labelHistory = QLabel("History :")
        self.textHistory = QTextEdit()
        self.textHistory.setFixedHeight(self.textHistory.fontMetrics().lineSpacing() * 10)
        self.textHistory.setText(self.interpolationDict['History'])
        self.textHistory.setReadOnly(True)
        self.textHistory.setStyleSheet("""
            QTextEdit[readOnly="true"] {
                background-color: #f8f8f8;
                border: 1px solid lightgray;
                font-family: Courier;
                font-size: 11;
            }
        """)

        labelComment = QLabel("Comment :")
        self.textComment = QTextEdit()
        self.textComment.setFixedHeight(self.textComment.fontMetrics().lineSpacing() * 10)
        self.textComment.setText(self.interpolationDict['Comment'])

        info_layout.addWidget(self.textName)
        info_layout.addWidget(labelHistory)
        info_layout.addWidget(self.textHistory)
        info_layout.addWidget(labelComment)
        info_layout.addWidget(self.textComment)
        info_layout.addStretch()

        info_tab.setLayout(info_layout)

        #----------------------------------------------
        self.tabs.addTab(pointers_tab, "Pointers")
        self.tabs.addTab(pointersPlot_tab, "Pointers plot")
        self.tabs.addTab(info_tab, "Info")
        self.tabs.setCurrentIndex(1)

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

        exit_shortcut = QShortcut(QKeySequence('Q'), self)
        exit_shortcut.activated.connect(self.close)

    #---------------------------------------------------------------------------------------------
    def contextMenuEvent(self, event):
        current_tab_index = self.tabs.currentIndex()
        if current_tab_index == 1:                  # Plot
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
    def closeEvent(self, event):
        self.interpolationDict['Comment'] = self.textComment.toPlainText()
        self.item.setData(0, Qt.UserRole, self.interpolationDict)
        self.open_displayWindows.pop(self.Id, None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(item):
        print('handle', item)

    app = QApplication([])

    X1Coords = [20,40,45,60,80]
    X2Coords = [30,50,65,80,90]

    itemDict = {
        'Id': 'abcd',
        'Name': 'A name',
        'Type': 'INTERPOLATION', 
        'interpolationMode': 'Linear',
        'X1Coords': X1Coords, 
        'X2Coords': X2Coords, 
        'X1Name': 'X1Name', 
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }

    item = QTreeWidgetItem()
    item.setData(0, Qt.UserRole, itemDict)

    open_displayWindows = {}
    Id_displayWindow = '1234'
    displayWindow = displayInterpolationWindow(Id_displayWindow, open_displayWindows, item)
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app.exec_())
