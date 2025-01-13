from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

from .misc import *
from .interactivePlot import interactivePlot
from .CustomQTableWidget import CustomQTableWidget

import sys
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch

from scipy import interpolate

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineInterpolationWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_interpolationWindows, items, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_interpolationWindows = open_interpolationWindows
        if len(items) == 2:
            self.itemINTERPOLATION = None
            self.items = items
        elif len(items) == 3:
            self.itemINTERPOLATION = items[0]
            self.items = items[1:]
        self.add_item_tree_widget = add_item_tree_widget

        self.serieWidth = 0.8
        self.pointerColor = 'blue'
        self.key_shift = False
        self.key_control = False
        self.key_x = False
        self.mousepress = None
        self.vline1 = None
        self.vline2 = None
        self.vline1List = []
        self.vline2List = []
        self.X1Coords = []
        self.X2Coords = []
        self.artistsList_Dict = {}
        self.interpolationMode = 'Linear'
        self.axsInterp = None
        self.second_xaxis = None

        title = 'Define INTERPOLATION : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)

        self.tabs = QTabWidget()

        #----------------------------------------------
        pointers_tab = QWidget()
        pointers_layout = QVBoxLayout()

        self.pointers_table = CustomQTableWidget()

        pointers_layout.addWidget(self.pointers_table)
        pointers_tab.setLayout(pointers_layout)

        #----------------------------------------------
        pointersPlot_tab = QWidget()
        pointersPlot_layout = QVBoxLayout()

        self.interactive_pointersPlot = interactivePlot()
        self.interactive_pointersPlot.right_margin = 100
        self.pointersPlot_ax = self.interactive_pointersPlot.axs[0]
        self.pointersPlot_axGradient = self.pointersPlot_ax.twinx()
        pointersPlot_layout.addWidget(self.interactive_pointersPlot.fig.canvas)

        pointersPlot_tab.setLayout(pointersPlot_layout)

        #----------------------------------------------
        plots_tab = QWidget()
        plots_layout = QVBoxLayout()

        self.interactive_plot = interactivePlot(rows=2, cols=1)
        self.interactive_plot.top_margin = 100
        self.interactive_plot.right_margin = 150
        self.axs = self.interactive_plot.axs
        plots_layout.addWidget(self.interactive_plot.fig.canvas)
        self.axsInterp = self.axs[0].twinx()
        self.axsInterp.sharey(self.axs[1])
        self.axsInterp.set_zorder(-10)

        plots_tab.setLayout(plots_layout)

        #----------------------------------------------
        self.tabs.addTab(plots_tab, "Plots")
        self.tabs.addTab(pointers_tab, "Pointers")
        self.tabs.addTab(pointersPlot_tab, "Pointers plot")
        self.tabs.setCurrentIndex(0)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)

        #----------------------------------------------
        control_layout = QHBoxLayout()

        self.showInterp = QCheckBox("Show Interpolated Curve")
        self.showInterp.setChecked(True)
        self.showInterp.setShortcut("Z")
        self.showInterp.setToolTip("Type key 'z' as shortcut")

        self.interp_combo_label = QLabel("Interpolation Method:")
        self.interp_combo_label.setToolTip("Choose between Linear or PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) interpolation")
        self.interp_combo = QComboBox()
        self.interp_combo.addItem("Linear")
        self.interp_combo.addItem("PCHIP")

        self.save_button = QPushButton("Save interpolation and serie interpolated", self)
        self.close_button = QPushButton("Close", self)

        control_layout.addStretch()
        control_layout.addWidget(self.showInterp)
        control_layout.addWidget(self.interp_combo_label)
        control_layout.addWidget(self.interp_combo)
        control_layout.addSpacing(50)
        control_layout.addWidget(self.save_button)
        control_layout.addWidget(self.close_button)

        main_layout.addLayout(control_layout)

        self.showInterp.stateChanged.connect(self.showInterp_change)
        self.interp_combo.currentIndexChanged.connect(self.interpMode_change)
        self.save_button.clicked.connect(self.save_serie)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        self.myplot()

        exit_shortcut = QShortcut(QKeySequence('Q'), self)
        exit_shortcut.activated.connect(self.close)

        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def showInterp_change(self):
        self.updateInterpPlot()

    #---------------------------------------------------------------------------------------------
    def interpMode_change(self):
        self.interpolationMode = self.interp_combo.currentText()
        self.updateInterpPlot()

    #---------------------------------------------------------------------------------------------
    def readINTERPOLATION(self):

        self.interpolationDict = self.itemINTERPOLATION.data(0, Qt.UserRole)
        self.X1Coords = self.interpolationDict['X1Coords']
        self.X2Coords = self.interpolationDict['X2Coords']

    #---------------------------------------------------------------------------------------------
    def myplot(self):

        if self.itemINTERPOLATION:
            self.readINTERPOLATION()

        self.drawPlots()
        self.drawConnections()
        self.updatePointers()
        self.updateInterpPlot()

    #---------------------------------------------------------------------------------------------
    def updateInterpPlot(self):

        self.axsInterp.set_visible(False)
        self.axsInterp.clear()
        self.interactive_plot.fig.canvas.draw()

        if len(self.X1Coords) < 2: return
        if not self.showInterp.isChecked(): return

        self.axsInterp.set_visible(True)

        f_1to2, f_2to1 = self.defineInterpolationFunctions(self.X1Coords, self.X2Coords, interpolationMode=self.interpolationMode)

        if self.second_xaxis: self.second_xaxis.remove()
        self.second_xaxis = self.axsInterp.secondary_xaxis('top', functions=(f_1to2, f_2to1))
        self.second_xaxis.tick_params(labelrotation=30)
        self.second_xaxis.set_xlabel(self.X2Name, color=self.serie2Color)
        plt.setp(self.second_xaxis.get_xticklabels(), horizontalalignment='left')

        X2Interp = f_2to1(self.X2)
        self.line2Interp, = self.axsInterp.plot(X2Interp, self.Y2, color=self.serie2Color, alpha=0.8, linewidth=self.serieWidth, label='line2Interp')
        self.axsInterp.set_ylabel(self.Y2Name, color=self.serie2Color)
        self.axsInterp.yaxis.set_label_position('right')
        self.interactive_plot.fig.canvas.draw()

    #---------------------------------------------------------------------------------------------
    def updatePointersPlot(self):

        self.pointersPlot_ax.set_visible(False)
        self.pointersPlot_axGradient.set_visible(False)
        self.pointersPlot_ax.clear()
        self.pointersPlot_axGradient.clear()
        self.interactive_pointersPlot.fig.canvas.draw()

        if len(self.X1Coords) < 2: return

        #------------------------------------------------
        self.pointersPlot_ax.set_visible(True)
        self.pointersPlot_axGradient.set_visible(True)

        line, = self.pointersPlot_ax.plot(self.X2Coords, self.X1Coords, color='steelblue', linewidth=1, label='aaaa')
        points = self.pointersPlot_ax.scatter(self.X2Coords, self.X1Coords, s=10, marker='o', color='steelblue')

        self.pointersPlot_ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=1)
        self.pointersPlot_ax.set_xlabel(self.X2Name)
        self.pointersPlot_ax.set_ylabel(self.X1Name)

        self.pointersPlot_axGradient.set_ylabel('Gradients', color='darkorange')
        self.pointersPlot_axGradient.yaxis.set_label_position('right') 

        X2CoordsValues = np.linspace(self.X2Coords[0], self.X2Coords[-1], 100)

        f_1to2, f_2to1 = self.defineInterpolationFunctions(self.X1Coords, self.X2Coords, interpolationMode='Linear')
        gradientLinear = np.gradient(f_2to1(X2CoordsValues), X2CoordsValues).astype(np.float32)      # to avoid unnecessary precision
        line1, = self.pointersPlot_axGradient.plot(X2CoordsValues, gradientLinear, color='darkorange', lw=1, label='Linear')

        f_1to2, f_2to1 = self.defineInterpolationFunctions(self.X1Coords, self.X2Coords, interpolationMode='PCHIP')
        gradientPCHIP = np.gradient(f_2to1(X2CoordsValues), X2CoordsValues).astype(np.float32)       # to avoid unnecessary precision
        line2, = self.pointersPlot_axGradient.plot(X2CoordsValues, gradientPCHIP, color='darkorange', linestyle='dashed', lw=1, label='PCHIP')

        lines = [line1, line2]
        labels = [line.get_label() for line in lines]
        self.pointersPlot_ax.legend(lines, labels)

        self.pointersPlot_axGradient.autoscale(axis='y', tight=False)

        self.pointersPlot_ax.patch.set_alpha(0)
        self.pointersPlot_axGradient.set_zorder(self.pointersPlot_ax.get_zorder() - 1)

        self.interactive_pointersPlot.fig.canvas.draw()

    #---------------------------------------------------------------------------------------------
    def updatePointers(self):

        self.X1Coords = sorted([float(line.get_xdata()[0]) for line in self.vline1List])
        self.X2Coords = sorted([float(line.get_xdata()[0]) for line in self.vline2List])

        self.pointers_table.clearContents()

        self.pointers_table.setRowCount(len(self.X1Coords))
        self.pointers_table.setColumnCount(2)
        self.pointers_table.setHorizontalHeaderLabels([self.X1Name, self.X2Name])
        self.pointers_table.resizeColumnsToContents()
        for i in range(len(self.X1Coords)):
            self.pointers_table.setItem(i, 0, QTableWidgetItem(str(f'{self.X1Coords[i]:.6f}')))
            self.pointers_table.setItem(i, 1, QTableWidgetItem(str(f'{self.X2Coords[i]:.6f}')))
            background_color = QColor('whitesmoke') if i % 2 == 0 else QColor('white')
            self.pointers_table.item(i, 0).setBackground(background_color)
            self.pointers_table.item(i, 1).setBackground(background_color)
        self.pointers_table.resizeColumnsToContents()

        self.updatePointersPlot()

    #---------------------------------------------------------------------------------------------
    def drawPlots(self):

        #----------------------------------------------------
        # self.axs[0] --> Reference 
        # self.axs[1] --> to interpolate

        #----------------------------------------------------
        self.serieDict = self.items[0].data(0, Qt.UserRole)
        self.X1Name = self.serieDict['X']
        self.Y1Name = self.serieDict['Y']
        self.serie1 = self.serieDict['Serie']
        self.serie1 = self.serie1.groupby(self.serie1.index).mean()
        self.X1 = self.serie1.index
        self.Y1 = self.serie1.values

        self.axs[0].grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        self.axs[0].set_xlabel(self.X1Name)
        self.axs[0].set_ylabel(self.Y1Name)
        self.axs[0].patch.set_alpha(0)
        self.axs[0].autoscale()

        self.serie1Color = self.serieDict['Color']
        self.serie1_Y_axisInverted = self.serieDict['Y axis inverted']
        self.axs[0].yaxis.set_inverted(self.serie1_Y_axisInverted)

        self.line1, = self.axs[0].plot(self.X1, self.Y1, color=self.serie1Color, linewidth=self.serieWidth, label='line1', picker=True, pickradius=20)
        self.points1 = self.axs[0].scatter(self.X1, self.Y1, s=5, marker='o', color=self.serie1Color, visible=False, label='points1', picker=True, pickradius=20)
        self.axs[0].line_points_pairs.append((self.line1, self.points1))

        self.linecursor1 = self.axs[0].axvline(color='k', alpha=0.25, linewidth=1)

        #----------------------------------------------------
        self.serieDict = self.items[1].data(0, Qt.UserRole)
        self.X2Name = self.serieDict['X']
        self.Y2Name = self.serieDict['Y']
        self.serie2 = self.serieDict['Serie']
        self.serie2 = self.serie2.groupby(self.serie2.index).mean()
        self.X2 = self.serie2.index
        self.Y2 = self.serie2.values

        self.axs[1].grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        self.axs[1].set_xlabel(self.X2Name)
        self.axs[1].set_ylabel(self.Y2Name)
        self.axs[1].patch.set_alpha(0)
        self.axs[1].autoscale()

        self.serie2Color = self.serieDict['Color']
        self.serie2_Y_axisInverted = self.serieDict['Y axis inverted']
        self.axs[1].yaxis.set_inverted(self.serie2_Y_axisInverted)

        self.line2, = self.axs[1].plot(self.X2, self.Y2, color=self.serie2Color, linewidth=self.serieWidth, label='line2', picker=True, pickradius=20)
        self.points2 = self.axs[1].scatter(self.X2, self.Y2, s=5, marker='o', color=self.serie2Color, visible=False, label='points2', picker=True, pickradius=20)
        self.axs[1].line_points_pairs.append((self.line2, self.points2))

        self.linecursor2 = self.axs[1].axvline(color='k', alpha=0.25, linewidth=1)

        #----------------------------------------------------
        self.interactive_plot.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.interactive_plot.fig.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.interactive_plot.fig.canvas.mpl_connect('pick_event', self.on_mouse_pick)
        self.interactive_plot.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)
        self.interactive_plot.fig.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.interactive_plot.fig.canvas.mpl_connect('scroll_event', self.on_mouse_scroll)

        #----------------------------------------------------
        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def drawConnections(self):

        for i in range(len(self.X1Coords)):
            X1Coord = self.X1Coords[i]
            X2Coord = self.X2Coords[i]
            vline1 = self.axs[0].axvline(X1Coord, color=self.pointerColor, alpha=0.5, linestyle='--', linewidth=1, label='vline1')
            vline2 = self.axs[1].axvline(X2Coord, color=self.pointerColor, alpha=0.5, linestyle='--', linewidth=1, label='vline2')
            self.vline1List.append(vline1)
            self.vline2List.append(vline2)
            connect = ConnectionPatch(color=self.pointerColor, alpha=0.5, linewidth=1, picker=10, clip_on=True, label='connection',
                        xyA=(X1Coord, self.axs[0].get_ylim()[0]), coordsA=self.axs[0].transData,
                        xyB=(X2Coord, self.axs[1].get_ylim()[1]), coordsB=self.axs[1].transData)
            self.interactive_plot.fig.add_artist(connect)
            self.artistsList_Dict[id(connect)] = [connect, vline1, vline2]

        self.interactive_plot.fig.canvas.draw()

    #---------------------------------------------------------------------------------------------
    def updateConnections(self):

        for artistsList in self.artistsList_Dict.values():
            if isinstance(artistsList[0], ConnectionPatch):
                connect = artistsList[0]
                x1, y1 = connect.xy1
                connect.xy1 = (x1, self.axs[0].get_ylim()[0])
                x2, y2 = connect.xy2
                connect.xy2 = (x2, self.axs[1].get_ylim()[1])
                if ((self.axs[0].get_xlim()[0] < x1 < self.axs[0].get_xlim()[1]) and
                    (self.axs[1].get_xlim()[0] < x2 < self.axs[1].get_xlim()[1])):
                    connect.set_visible(True)
                else:
                    connect.set_visible(False)

        self.interactive_plot.fig.canvas.draw()

    #---------------------------------------------------------------------------------------------
    def deleteConnections(self):

        for objectId in self.artistsList_Dict.keys():
            for artist in self.artistsList_Dict[objectId]:
                artist.remove()
        self.artistsList_Dict = {}
        self.vline1List = []
        self.vline2List = []

    #---------------------------------------------------------------------------------------------
    def deleteCoords(self):
    
        self.X1Coords = []
        self.X2Coords = []

    #---------------------------------------------------------------------------------------------
    def on_key_press(self, event):

        sys.stdout.flush()

        #-------------------
        if event.key == 'c':
            if self.vline1 != None and self.vline2 != None :
                X1Coord = float(self.vline1.get_xdata()[0])
                X2Coord = float(self.vline2.get_xdata()[0])
                # current X1Coords, X2Coords. Will be defined later from setInterp
                X1Coords_cur = sorted([float(line.get_xdata()[0]) for line in self.vline1List])
                X2Coords_cur = sorted([float(line.get_xdata()[0]) for line in self.vline2List])
                # Check positions
                if np.searchsorted(X1Coords_cur, X1Coord) != np.searchsorted(X2Coords_cur, X2Coord):
                    msg = 'Error: Connection not possible because it would cross existing connections'
                    self.status_bar.showMessage(msg, 5000)
                    return

                connect = ConnectionPatch(color=self.pointerColor, alpha=0.5, linewidth=1, picker=10, clip_on=True, label='connection',
                            xyA=(X1Coord, self.axs[0].get_ylim()[0]), coordsA=self.axs[0].transData,
                            xyB=(X2Coord, self.axs[1].get_ylim()[1]), coordsB=self.axs[1].transData)
                self.interactive_plot.fig.add_artist(connect)
                self.artistsList_Dict[id(connect)] = [connect, self.vline1, self.vline2]
                self.vline1List.append(self.vline1)
                self.vline2List.append(self.vline2)
                self.vline1 = None
                self.vline2 = None

                self.updatePointers()
                self.updateInterpPlot()
                self.interactive_plot.fig.canvas.draw()

        #-------------------
        elif event.key == 'a':
            self.updateConnections()

        #-------------------
        elif event.key == 'x':
            self.key_x = True 

        #-------------------
        elif event.key == 'X':
            reply = QMessageBox.question(
                self, 
                'Confirmation', 
                'Are you sure you want to delete all pointers ?', 
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.deleteConnections()
                self.deleteCoords()
                self.updatePointers()
                self.updateInterpPlot()
                self.interactive_plot.fig.canvas.draw()

        #-------------------
        elif event.key == 'shift':
            self.key_shift = True

        #-------------------
        elif event.key == 'control':
            self.key_control = True

    #------------------------------------------------------------------
    def on_key_release(self, event):

        sys.stdout.flush()

        #-------------------
        if event.key == 'x':
            self.key_x = False

        #-------------------
        elif event.key == 'shift':
            self.key_shift = False

        #-------------------
        elif event.key == 'control':
            self.key_control = False 

    #------------------------------------------------------------------
    def on_mouse_press(self, event):

        if event.inaxes not in self.axs: return

        self.mousepress = None
        if event.button == 1:
            self.mousepress = 'left'

    #------------------------------------------------------------------
    def on_mouse_scroll(self, event):

        self.updateConnections()

    #------------------------------------------------------------------
    def on_mouse_pick(self, event):
    
        artistLabel = event.artist.get_label()
   
        #-----------------------------------------------
        if artistLabel == 'connection':
            if self.key_x:
                objectId = id(event.artist)
                for artist in self.artistsList_Dict[objectId]:
                    artist.remove()
                    if artist in self.vline1List:
                        self.vline1List.remove(artist)
                    if artist in self.vline2List:
                        self.vline2List.remove(artist)
                del self.artistsList_Dict[objectId]

                self.updatePointers()
                self.updateInterpPlot()
                
        #-----------------------------------------------
        if artistLabel in ['line1', 'line2']:
            if self.key_shift:
                coordPoint = [event.mouseevent.xdata, event.mouseevent.ydata]
                if event.artist == self.line1:
                    if self.vline1 != None:
                        self.vline1.set_data([coordPoint[0], coordPoint[0]], [0, 1])
                    else:
                        self.vline1 = self.axs[0].axvline(coordPoint[0], color=self.pointerColor , alpha=0.5, linestyle='--', linewidth=1, label='vline1')
                elif event.artist == self.line2:
                    if self.vline2 != None:
                        self.vline2.set_data([coordPoint[0], coordPoint[0]], [0, 1])
                    else:
                        self.vline2 = self.axs[1].axvline(coordPoint[0], color=self.pointerColor, alpha=0.5, linestyle='--', linewidth=1, label='vline2')
                self.interactive_plot.fig.canvas.draw()
   
        #-----------------------------------------------
        elif artistLabel in ['points1', 'points2']:
            if self.key_control:
                ind = event.ind[0]
                if event.artist == self.points1:
                    coordPoint = [self.X1[ind], self.Y1[ind]]
                    if self.vline1 != None:
                        self.vline1.set_data([coordPoint[0], coordPoint[0]], [0, 1])
                    else:
                        self.vline1 = self.axs[0].axvline(coordPoint[0], color=self.pointerColor , alpha=0.5, linestyle='--', linewidth=1, label='vline1')
                elif event.artist == self.points2:
                    coordPoint = [self.X2[ind], self.Y2[ind]]
                    if self.vline2 != None:
                        self.vline2.set_data([coordPoint[0], coordPoint[0]], [0, 1])
                    else:
                        self.vline2 = self.axs[1].axvline(coordPoint[0], color=self.pointerColor, alpha=0.5, linestyle='--', linewidth=1, label='vline2')
                self.interactive_plot.fig.canvas.draw()

    #------------------------------------------------------------------
    def on_mouse_motion(self, event):

        #-----------------------------------------------
        found = False
        for artistsList in self.artistsList_Dict.values():
            if isinstance(artistsList[0], ConnectionPatch):
                connect = artistsList[0]
                if connect.contains(event)[0]:
                    connect.set_color('red')
                    found = True 
                else:
                    connect.set_color(self.pointerColor)
        if found:
            self.interactive_plot.fig.canvas.draw()
            #self.interactive_plot.fig.canvas.draw_idle()

        #-----------------------------------------------
        if event.inaxes is self.interactive_plot.axs[0]:
            self.linecursor1.set_visible(True)
            self.linecursor2.set_visible(False)
            self.linecursor1.set_xdata([event.xdata])
        elif event.inaxes is self.interactive_plot.axs[1]:
            self.linecursor1.set_visible(False)
            self.linecursor2.set_visible(True)
            self.linecursor2.set_xdata([event.xdata])
        else:
            self.linecursor1.set_visible(False)
            self.linecursor2.set_visible(False)
            self.points1.set_visible(False)
            self.points2.set_visible(False)
        self.interactive_plot.fig.canvas.draw()

        #-----------------------------------------------
        if self.mousepress == 'left':
            self.updateConnections()

    #---------------------------------------------------------------------------------------------
    @staticmethod
    def safe_PchipInterpolator(X1Coords, X2Coords):
        f_pchip = interpolate.PchipInterpolator(X1Coords, X2Coords, extrapolate=False)
    
        def extrapolated_func(x):
            if x < X1Coords[0]:
                slope = (X2Coords[1] - X2Coords[0]) / (X1Coords[1] - X1Coords[0])
                return X2Coords[0] + slope * (x - X1Coords[0])
            elif x > X1Coords[-1]:
                slope = (X2Coords[-1] - X2Coords[-2]) / (X1Coords[-1] - X1Coords[-2])
                return X2Coords[-1] + slope * (x - X1Coords[-1])
            else:
                return f_pchip(x)
    
        return np.vectorize(extrapolated_func, otypes=[float])  

    #---------------------------------------------------------------------------------------------
    @staticmethod
    def defineInterpolationFunctions(X1Coords, X2Coords, interpolationMode='Linear'):
        if interpolationMode == 'Linear':
            f_1to2 = interpolate.interp1d(X1Coords, X2Coords, kind='linear', fill_value='extrapolate')
            f_2to1 = interpolate.interp1d(X2Coords, X1Coords, kind='linear', fill_value='extrapolate')
        elif interpolationMode == 'PCHIP':
            #f_1to2 = interpolate.PchipInterpolator(X1Coords, X2Coords, extrapolate=True)
            #f_2to1 = interpolate.PchipInterpolator(X2Coords, X1Coords, extrapolate=True)
            f_1to2 = defineInterpolationWindow.safe_PchipInterpolator(X1Coords, X2Coords)
            f_2to1 = defineInterpolationWindow.safe_PchipInterpolator(X2Coords, X1Coords)

        return (f_1to2, f_2to1)

    #---------------------------------------------------------------------------------------------
    def save_serie(self):

        if len(self.X1Coords) < 2: 
            msg = 'Error: interpolation function not defined (not enough pointers)'
            self.status_bar.showMessage(msg, 5000)
            return

        interpolation_Id = generate_Id()
        interpolationDict = {
            'Id': interpolation_Id,
            'Type': 'INTERPOLATION',
            'Name': '', 
            'X1Coords': self.X1Coords,
            'X2Coords': self.X2Coords,
            'X1Name': self.X1Name,              # interpolated to reference that is X1
            'Comment': '',
            'History': '',
        }
        self.add_item_tree_widget(self.items[1].parent(), interpolationDict)

        f_1to2, f_2to1 = self.defineInterpolationFunctions(self.X1Coords, self.X2Coords, interpolationMode=self.interpolationMode)

        interpolated_Id = generate_Id()
        interpolated_serieDict = self.serieDict | {'Id': interpolated_Id, 
            'Type': 'Serie interpolated', 
            'Serie': pd.Series(self.Y2, index=f_2to1(self.X2)),
            'InterpolationMode': self.interpolationMode,
            'X': self.X1Name,
            'XOriginal': self.X2Name,
            'XOriginalValues': self.X2,
            'X1Coords': self.X1Coords,
            'X2Coords': self.X2Coords,
            'Color': generate_color(exclude_color=self.serieDict['Color']),
            'History': append_to_htmlText(self.serieDict['History'], 
                f'serie <i><b>{self.serieDict["Id"]}</i></b> interpolated with INTERPOLATION <i><b>{interpolation_Id}</i></b> with mode {self.interpolationMode}<BR>---> serie <i><b>{interpolated_Id}</b></i>'),
            'Comment': ''
        }
        position = self.items[1].parent().indexOfChild(self.items[1])
        self.add_item_tree_widget(self.items[1].parent(), interpolated_serieDict, position+1)

    #---------------------------------------------------------------------------------------------
    def sync_with_item(self, item):
        if not item in self.items: return

        self.raise_()

        self.deleteConnections()
        self.axs[0].clear()
        self.axs[1].clear()
        self.axsInterp.clear()
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def contextMenuEvent(self, event):
        current_tab_index = self.tabs.currentIndex()
        if current_tab_index == 0:                  # Plot
            context_menu = QMenu(self)
            print_action = QAction("Save plot as PNG or PDF", self)
            print_action.triggered.connect(self.savePlot)
            context_menu.addAction(print_action)
            context_menu.exec_(event.globalPos())

    #---------------------------------------------------------------------------------------------
    def savePlot(self):
        fileName, _ = QFileDialog.getSaveFileName(self, 'Save Plots', '', 'PNG Files (*.png);;PDF Files (*.pdf)')
        if fileName:
            self.linecursor1.set_visible(False)
            self.linecursor2.set_visible(False)
            plt.savefig(fileName)
            self.linecursor1.set_visible(True)
            self.linecursor2.set_visible(True)

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.open_interpolationWindows.pop(self.Id, None)
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

    open_interpolationWindows = {}
    Id_interpolationWindow = '1234'
    interpolationWindow = defineFilterWindow(Id_interpolationWindow, open_interpolationWindows, item, handle_item)
    open_interpolationWindows[Id_interpolationWindow] = interpolationWindow
    interpolationWindow.show()

    sys.exit(app.exec_())
