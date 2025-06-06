from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import pandas as pd
import numpy as np

from .misc import *
from .CustomQTableWidget import CustomQTableWidget 

#=========================================================================================
class importDataWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, open_importWindow, add_item_tree_widget):
        super().__init__()

        self.open_importWindow = open_importWindow
        self.add_item_tree_widget = add_item_tree_widget

        title = 'Data importer'
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 800, 600)
        
        #----------------------------------------------
        self.label = QLabel("Press 'Ctrl+V' (or 'Cmd+V' on Mac) to paste the copied spreadsheet data.", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            "padding: 10px;"
        )

        #----------------------------------------------
        self.data_table = CustomQTableWidget()

        #----------------------------------------------
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.data_table)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        self.importPointers_button = QPushButton("Import pointers", self)
        self.importPointers_button.setStyleSheet("padding: 4px 12px;")
        self.importPointers_button.setToolTip("(Distorded, Reference)")
        self.importSeries_button = QPushButton("Import series", self)
        self.importSeries_button.setStyleSheet("padding: 4px 12px;")
        self.importSeries_button.setToolTip("(X,Y) or (X,Y1,Y2,...)")
        self.close_button = QPushButton("Close", self)
        button_layout.addStretch()

        button_layout.addWidget(self.importSeries_button)
        button_layout.addWidget(self.importPointers_button)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.importSeries_button.clicked.connect(self.import_series)
        self.importPointers_button.clicked.connect(self.import_pointers)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        menu_bar = QMenuBar(self)
        main_layout.setMenuBar(menu_bar)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        paste_shortcut = QShortcut('Ctrl+v', self)
        paste_shortcut.activated.connect(self.paste_data)

    #---------------------------------------------------------------------------------------------
    def paste_data(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text:
            QMessageBox.warning(self, "No Data", "The clipboard is empty.")
            return

        rows = text.split("\n")
        #clean_rows = [row.strip() for row in rows if row.strip()]
        clean_rows = [row for row in rows if row.strip('\n')]

        if not clean_rows:
            QMessageBox.warning(self, "Invalid Data", "No valid data found in clipboard.")
            return

        expected_columns = len(clean_rows[0].split('\t'))
        #print(expected_columns)

        data = []
        for n, row in enumerate(clean_rows):
            columns = row.split("\t")
            #print('----', n, columns)
            values = [""] * expected_columns
            for i in range(len(columns)):
                values[i] = columns[i] 
            data.append(values)

        if not data:
            QMessageBox.warning(self, "Invalid Data", "At least 2 columns (X,Y), (X,Y1,Y2,...) or (X Reference, X Distorded)")
            return

        headers = data.pop(0)
        self.populate_table(data, headers)

    #---------------------------------------------------------------------------------------------
    def populate_table(self, data, headers):
        # Set headers
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)

        # Populate rows
        self.data_table.setRowCount(len(data))
        for row_index, row_data in enumerate(data):
            for col_index, cell in enumerate(row_data):
                self.data_table.setItem(row_index, col_index, QTableWidgetItem(cell))
                if cell == '':
                    base = QColor('peachpuff')
                    alt = QColor('white') if row_index % 2 else QColor('whitesmoke')
                    background_color = blend_colors(base, alt, ratio=0.6)
                else:
                    background_color = QColor('whitesmoke') if row_index % 2 == 0 else QColor('white')
                self.data_table.item(row_index, col_index).setBackground(background_color)

        self.data_table.resizeColumnsToContents()
        self.data_table.horizontalHeader().setSectionsMovable(True)
        self.data_table.set_italic_headers()

    #---------------------------------------------------------------------------------------------
    def is_numeric(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    #---------------------------------------------------------------------------------------------
    def data_table_headers_check(self):

        for col in range(self.data_table.columnCount()):
            header = self.data_table.horizontalHeaderItem(col).text()
            if not self.is_numeric(header):
                return True
            else:
                return False

    #---------------------------------------------------------------------------------------------
    def data_table_values_check(self, allow_empty_cells=False):

        for col in range(self.data_table.columnCount()):
            for row in range(self.data_table.rowCount()):
                item = self.data_table.item(row, col)
                if allow_empty_cells:
                    if item.text() != "" and not self.is_numeric(item.text()):
                        return False
                else:
                    if not self.is_numeric(item.text()):
                        return False
        return True

    #---------------------------------------------------------------------------------------------
    def data_table_check(self, allow_empty_cells=False):

        if self.data_table.rowCount() == 0:
            msg = 'Error: No data to import'
            self.status_bar.showMessage(msg, 5000)
            return False

        if not self.data_table_headers_check():
            msg = 'Error: Headers are not text'
            self.status_bar.showMessage(msg, 5000)
            return False

        if not self.data_table_values_check(allow_empty_cells):
            msg = 'Error: Values are not numeric'
            self.status_bar.showMessage(msg, 5000)
            return False

        return True

    #---------------------------------------------------------------------------------------------
    def is_monotonic_increasing_and_unique(self, values):
   
        serie = pd.Series(values)
        #print(serie.is_monotonic_increasing, serie.is_unique)
        is_monotonic = serie.is_monotonic_increasing and serie.is_unique
    
        return is_monotonic

    #---------------------------------------------------------------------------------------------
    def import_series(self):
    
        if self.data_table.columnCount() < 2:
            QMessageBox.warning(self, "Import series", "Import not possible. Expected format is at least 2 columns (X,Y) or (X,Y1,Y2,...)")
            return
    
        if not self.data_table_check(allow_empty_cells=True): 
            return
    
        valid_rows = []
        index = []
        for row in range(self.data_table.rowCount()):
            item = self.data_table.item(row, 0)
            if item is not None:
                text = item.text().strip()
                if text != '':
                    try:
                        val = float(text)
                        index.append(val)
                        valid_rows.append(row)
                    except ValueError:
                        pass
    
        if not index:
            QMessageBox.warning(self, "Import series", "No valid index values found in the first column.")
            return
    
        X = self.data_table.horizontalHeaderItem(0).text()
    
        for col in range(1, self.data_table.columnCount()):
    
            values = []
            for row in valid_rows:
                item = self.data_table.item(row, col)
                valueText = item.text().strip() if item is not None else ''
                if valueText == '':
                    value = np.nan
                else:
                    try:
                        value = float(valueText)
                    except ValueError:
                        value = np.nan
                values.append(value)
    
            Y = self.data_table.horizontalHeaderItem(col).text()
    
            serie_Id = generate_Id()
            serieDict = {
                'Id': serie_Id,
                'Type': 'Serie',
                'Name': '',
                'X': X,
                'Y': Y,
                'Y axis inverted': False,
                'Color': generate_color(),
                'History': 'Imported serie',
                'Comment': '',
                'Serie': pd.Series(values, index=index),
            }
            self.add_item_tree_widget(None, serieDict)
    
            msg = f'{X} / {Y} imported as serie {serie_Id}'
            self.status_bar.showMessage(msg, 2000)

    #---------------------------------------------------------------------------------------------
    def import_pointers(self):

        if self.data_table.columnCount() < 2:
            QMessageBox.warning(self, "Import pointers", "Import not possible. Expected format is 2 columns (X Reference, X Distorded)")
            return

        if not self.data_table_check(): return

        # column order may have been changed
        header = self.data_table.horizontalHeader()
        column_order = [header.logicalIndex(i) for i in range(self.data_table.columnCount())]

        # Distorded (X2Coords), Reference (X1Coords) as columns
        X2Coords = [float(self.data_table.item(row, column_order[0]).text()) for row in range(self.data_table.rowCount())] 
        X1Coords = [float(self.data_table.item(row, column_order[1]).text()) for row in range(self.data_table.rowCount())] 
        X2Name = self.data_table.horizontalHeaderItem(column_order[0]).text()
        X1Name = self.data_table.horizontalHeaderItem(column_order[1]).text()

        if not self.is_monotonic_increasing_and_unique(X2Coords):
            QMessageBox.warning(self, "Import pointers", f"Import not possible : {X2Name} values must be monotonic increasing and unique")
            return
        if not self.is_monotonic_increasing_and_unique(X1Coords):
            QMessageBox.warning(self, "Import pointers", f"Import not possible : {X1Name} values must be monotonic increasing and unique")
            return

        item_Id =  generate_Id()
        itemDict = {
            'Id': item_Id, 
            'Type': 'INTERPOLATION', 
            'X1Coords': X1Coords,
            'X2Coords': X2Coords,
            'X1Name': X1Name,
            'History': 'Imported INTERPOLATION',
            'Name': '', 
            'Comment': '',
            }
        self.add_item_tree_widget(None, itemDict)          # will be added on parent from current index
        #print(f"{X} / {Y}")

        msg = f'Interpolation pointers with {X1Name} for reference imported as INTERPOLATION {item_Id}'
        self.status_bar.showMessage(msg, 2000)

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.open_importWindow.pop('123456', None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(parent, item):
        print('handle', parent, item)

    app = QApplication([])

    Id_importWindow = '1234'
    open_importWindow = {}

    importWindow = importDataWindow(open_importWindow, handle_item)
    open_importWindow[Id_importWindow] = importWindow
    importWindow.show()

    sys.exit(app.exec_())

