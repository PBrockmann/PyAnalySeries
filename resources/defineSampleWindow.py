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
from scipy.integrate import fixed_quad

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineSampleWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_sampleWindows, items, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_sampleWindows = open_sampleWindows
        self.items = items
        self.add_item_tree_widget = add_item_tree_widget

        self.item = items[0]
        if len(self.items) == 2:
            self.itemRef = items[1]
        else: 
            self.itemRef = None
        self.serieWidth = 0.8
        self.step = 25
        self.kind = 'linear' 
        self.integrated = False

        title = 'Define SAMPLE : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters')
        groupbox1_layout = QVBoxLayout()
        groupbox1.setFixedHeight(150)

        # ===== 
        self.group = QButtonGroup(self)

        self.step_radio = QRadioButton("Sampling with step :")
        self.step_spinbox = QDoubleSpinBox()
        self.step_spinbox.setRange(0, 1000)
        self.step_spinbox.setSingleStep(5)
        self.step_spinbox.setValue(self.step)
        self.step_spinbox.setDecimals(2)
        self.step_spinbox.setFixedWidth(80)

        step_layout = QHBoxLayout()
        step_layout.addWidget(self.step_radio)
        step_layout.addWidget(self.step_spinbox)
        step_layout.addStretch()

        self.xvalues_radio = QRadioButton("Sampling using x values of")
        self.xvalues_label = QLabel('None')
        font = QFont("Courier New", 12)
        self.xvalues_label.setFont(font)

        xvalues_layout = QHBoxLayout()
        xvalues_layout.addWidget(self.xvalues_radio)
        xvalues_layout.addWidget(self.xvalues_label)
        xvalues_layout.addStretch()

        self.group.addButton(self.step_radio)
        self.group.addButton(self.xvalues_radio)

        groupbox1_layout.addLayout(step_layout)
        groupbox1_layout.addLayout(xvalues_layout)

        if self.itemRef:
            self.xvalues_radio.setChecked(True)
            self.serieRefDict = self.itemRef.data(0, Qt.UserRole)
            self.serieRef_XName = self.serieRefDict['X']
            self.serieRef_YName = self.serieRefDict['Y']
            self.serieRef_Id = self.serieRefDict['Id']
            self.xvalues_label.setText(f'{self.serieRef_Id}: {self.serieRef_XName} / {self.serieRef_YName}')
            self.sample_from_xvalues = True 
        else:
            self.step_radio.setChecked(True)
            self.xvalues_radio.setEnabled(False)
            self.xvalues_label.setEnabled(False)
            self.sample_from_xvalues = False

        # ===== 
        kind_layout = QHBoxLayout()
        label_s2 = QLabel('Kind of interpolation :')
        self.kind_dropdown = QComboBox()
        self.kind_dropdown.addItems([
             'nearest', 'zero', 'linear', 'quadratic', 'cubic'
        ])
        self.kind_dropdown.setFixedWidth(100)
        self.kind_dropdown.setCurrentText(self.kind)
        kind_layout.addWidget(label_s2)
        kind_layout.addWidget(self.kind_dropdown)
        kind_layout.addStretch()

        integrated_layout = QHBoxLayout()
        label_s3 = QLabel('Integration :')
        self.integrated_checkbox = QCheckBox()
        self.integrated_checkbox.setChecked(self.integrated)
        integrated_layout.addWidget(label_s3)
        integrated_layout.addWidget(self.integrated_checkbox)
        integrated_layout.addStretch()

        groupbox1_layout.addLayout(kind_layout)
        groupbox1_layout.addLayout(integrated_layout)
        groupbox1_layout.addStretch()

        # ===== 
        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1)

        #----------------------------------------------
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_value)

        self.step_spinbox.editingFinished.connect(self.check_value_step)
        self.step_radio.toggled.connect(self.delayed_update)
        self.xvalues_radio.toggled.connect(self.delayed_update)
        self.kind_dropdown.currentIndexChanged.connect(self.delayed_update)
        self.integrated_checkbox.stateChanged.connect(self.delayed_update)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()
        self.myplot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save sample and serie sampled", self)
        self.save_button.setStyleSheet("padding: 4px 12px;")
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

        self.status_bar.showMessage('Ready', 5000)

    #---------------------------------------------------------------------------------------------
    def check_value_step(self):
        if self.step_spinbox.value() == 0.0:
            QMessageBox.warning(self, "Invalid Value", "Zero is not allowed.")
            self.step_spinbox.setValue(5)  # Set to a default non-zero value
        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def delayed_update(self):
        self.status_bar.showMessage('Waiting', 1000)
        self.update_timer.start(1000)

    #---------------------------------------------------------------------------------------------
    def update_value(self):

        self.step = self.step_spinbox.value()
        self.kind = self.kind_dropdown.currentText()
        self.sample_from_xvalues = self.xvalues_radio.isChecked()
        self.integrated = self.integrated_checkbox.isChecked()

        xlim = self.interactive_plot.axs[0].get_xlim()
        ylim = self.interactive_plot.axs[0].get_ylim()
        self.interactive_plot.axs[0].clear()
        self.myplot(limits=[xlim,ylim])

    #---------------------------------------------------------------------------------------------
    def myplot(self, limits=None):

        self.interactive_plot.reset()

        self.serieDict = self.item.data(0, Qt.UserRole)
        self.xName = self.serieDict['X']
        self.yName = self.serieDict['Y']
        self.serie = self.serieDict['Serie']
        self.serie = self.serie.groupby(self.serie.index).mean()

        if self.sample_from_xvalues:
            self.serieRefDict = self.itemRef.data(0, Qt.UserRole)
            self.serieRef = self.serieRefDict['Serie']
            self.sample_index = self.serieRef.index
        else:
            index_min = self.serie.index.min()
            index_max = self.serie.index.max()
            index_min = np.ceil(index_min / self.step) * self.step
            index_max = np.floor(index_max / self.step) * self.step
            self.sample_index = np.arange(index_min, index_max + self.step, self.step)

        ax = self.interactive_plot.axs[0]

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)
        ax.autoscale()

        serieSampled = self.sample(self.serie, self.sample_index, self.kind, integrated=self.integrated, ax=ax)
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
        for legend_line, ax_line in zip(legend.get_lines(), ax.get_lines()[-2:]):       # [-2:] to remove ax.axvline
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

    #----------------------------------------------------------------------------------
    @staticmethod
    def sample(serie, sample_index, kind="linear", integrated=False, ax=None, quad_points=20):
        """
        Interpolates or integrates a time series on specified sample points.
    
        Parameters:
            serie (pd.Series): Time series with index as x-values.
            sample_index (np.ndarray): Points where values are interpolated or integrated.
            kind (str): Interpolation type ('linear', 'cubic', etc.).
            integrated (bool): If True, use integration-based sampling.
            ax (matplotlib axis, optional): For visualizing integration intervals.
            quad_points (int): Number of points for fixed quadrature if integrated=True.
    
        Returns:
            pd.Series: Sampled values at specified indices.
        """
    
        # Remove duplicate indices and keep the mean
        serie = serie.groupby(serie.index).mean()
    
        # Restrict to range of data
        x_min, x_max = serie.index.min(), serie.index.max()
        valid_sample_index = sample_index[(sample_index >= x_min) & (sample_index <= x_max)]
    
        if not integrated:
            # Standard interpolation
            result_serie = pd.Series(index=valid_sample_index, dtype=float)
            result_serie = result_serie.combine_first(serie).sort_index()
            result_serie = result_serie.interpolate(method=kind, limit_direction="both")
            return result_serie.loc[valid_sample_index]
        else:
            # Integrated interpolation using fixed_quad
            interpolator = interpolate.interp1d(serie.index, serie.values, kind=kind, fill_value="extrapolate")
  
            # Compute midpoints between valid sample points
            mids = (valid_sample_index[1:] + valid_sample_index[:-1]) / 2

            # Compute extended edges for first and last interval
            first_edge = valid_sample_index[0] - (mids[0] - valid_sample_index[0])
            last_edge = valid_sample_index[-1] + (valid_sample_index[-1] - mids[-1])
            
            # Combine all edges
            edges = [first_edge] + list(mids) + [last_edge]
            result_index = valid_sample_index  # Each interval is associated with a sample point
 
            # Create full list of intervals and associated result index
            intervals = []
            filtered_index = []
            
            for i in range(len(result_index)):
                a = edges[i]
                b = edges[i + 1]
            
                if a >= x_min and b <= x_max:
                    intervals.append((a, b))
                    filtered_index.append(result_index[i])

            # Perform integration
            integrated_values = []
            for (a, b) in intervals:
                integral_value, _ = fixed_quad(interpolator, a, b, n=quad_points)
                mean_value = integral_value / (b - a)
                integrated_values.append(mean_value)
            
                # Optional: visualize integration interval
                if ax is not None:
                    line1 = ax.axvline(a, color="blue", linestyle="--", alpha=0.4, lw=0.5)
                    line2 = ax.axvline(b, color="blue", linestyle="--", alpha=0.4, lw=0.5)
    
            return pd.Series(data=integrated_values, index=filtered_index)

    #---------------------------------------------------------------------------------------------
    def save_serie(self):
        sample_Id = generate_Id()
        if not self.sample_from_xvalues:
            sampleDict = {
                'Id': sample_Id,
                'Type': 'SAMPLE', 
                'Name': f'Sample every {self.step}', 
                'Parameters': f'{self.step} ; {self.kind}; {self.integrated}',
                'Comment': '',
                'History': f'<BR>Sample with parameters :' + \
                        '<ul>' + \
                        f'<li>Step : {self.step}' + \
                        f'<li>Kind of interpolation : {self.kind}' + \
                        f'<li>Integrated : {self.integrated}' + \
                        '</ul>'
            }
        else:
            sampleDict = {
                'Id': sample_Id,
                'Type': 'SAMPLE', 
                'Name': f'Sample using x values of {self.serieRef_YName}',
                'Parameters': f'{self.kind} ; {self.integrated}',
                'Comment': '',
                'History': f'<BR>Sample with parameters :' + \
                        '<ul>' + \
                        f'<li>X values from {self.serieRef_Id} : {self.serieRef_XName} / {self.serieRef_YName}' + \
                        f'<li>Kind of interpolation : {self.kind}' + \
                        f'<li>Integrated : {self.integrated}' + \
                        '</ul>',
                'XCoords': self.sample_index
            }
        self.add_item_tree_widget(self.item.parent(), sampleDict)

        sampled_Id = generate_Id()
        if not self.sample_from_xvalues:
            textHistory = f'every {self.step} and {self.kind} interpolation with integration at {self.integrated}'
        else:
            textHistory = f'using x values from {self.serieRef_YName} and {self.kind} interpolation with integration at {self.integrated}'

        sampled_serieDict = self.serieDict | {'Id': sampled_Id, 
            'Type': 'Serie sampled', 
            'Serie': self.sample(self.serie, self.sample_index, kind=self.kind, integrated=self.integrated),
            'Color': generate_color(exclude_color=self.serieDict['Color']),
            'History': append_to_htmlText(self.serieDict['History'], 
                f'<BR>Serie <i><b>{self.serieDict["Id"]}</i></b> sampled {textHistory} with SAMPLE <i><b>{sample_Id}</i></b><BR>---> serie <i><b>{sampled_Id}</b></i>'),
            'Comment': '',
        }

        try:
            position = self.item.parent().indexOfChild(self.item)
            self.add_item_tree_widget(self.item.parent(), sampled_serieDict, position+1)
        except:
            pass 

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

    #---------------------------------
    x1 = np.arange(0, 10+0.1, 0.1)
    y1 = np.sin(x1)
    x2 = np.arange(-10, 20+1, 1)
    random_values = np.random.uniform(-10, 20, 10)  # Générer n valeurs entre a et b
    x2 = np.sort(random_values)
    y2 = np.cos(x2)

    #---------------------------------
    np.random.seed(42)
    x1 = np.linspace(0, 10, 500)
    y1 = np.sin(2 * np.pi * x1) + 0.5 * np.sin(10 * np.pi * x1)  # Signal HF
    y1 += np.random.normal(scale=0.1, size=len(y1))  # Add noise

    #x2 = np.linspace(0, 10, 21)
    x2 = [ 1, 1.5, 2, 2.2, 5, 6, 8.5, 9]
    y2 = np.cos(x2)

    #---------------------------------
    serie1 = pd.Series(y1, index=x1)

    serie1Dict = {'Id': 'abcd', 'X': 'xName', 'Y': 'yName', 'Serie': serie1, 
            'Color': 'darkorange', "Y axis inverted": True, 
            'Comment': 'A text', 'History': 'command1 ; command2'}
    item1 = QTreeWidgetItem()
    item1.setData(0, Qt.UserRole, serie1Dict)

    #---------------------------------
    serie2 = pd.Series(y2, index=x2)

    serie2Dict = {'Id': 'abcd', 'X': 'xName', 'Y': 'yName', 'Serie': serie2, 
            'Color': 'darkorange', "Y axis inverted": True, 
            'Comment': 'A text', 'History': 'command1 ; command2'}
    item2 = QTreeWidgetItem()
    item2.setData(0, Qt.UserRole, serie2Dict)

    #---------------------------------
    items = []
    items.append(item1)
    items.append(item2)

    open_sampleWindows = {}
    Id_sampleWindow = '1234'
    sampleWindow = defineSampleWindow(Id_sampleWindow, open_sampleWindows, items, handle_item)
    open_sampleWindows[Id_sampleWindow] = sampleWindow
    sampleWindow.show()

    sys.exit(app.exec_())

