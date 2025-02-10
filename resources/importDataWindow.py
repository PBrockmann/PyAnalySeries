from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import pandas as pd

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
        self.importPointers_button.setToolTip("Order colums as Reference, Distorded")
        self.importSeries_button = QPushButton("Import series", self)
        self.importSeries_button.setToolTip("Order colums as X values, Y1 values, (Y2 values, ...)")
        self.close_button = QPushButton("Close", self)
        button_layout.addStretch()

        button_layout.addWidget(self.importPointers_button)
        button_layout.addWidget(self.importSeries_button)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.importPointers_button.clicked.connect(self.import_pointers)
        self.importSeries_button.clicked.connect(self.import_series)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        menu_bar = QMenuBar(self)
        main_layout.setMenuBar(menu_bar)
        edit_menu = menu_bar.addMenu("Edit")

        paste_action = QAction("Paste", self)
        paste_action.setShortcut('Ctrl+v')
        paste_action.triggered.connect(self.paste_data)
        edit_menu.addAction(paste_action)

    #---------------------------------------------------------------------------------------------
    def paste_data(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text:
            QMessageBox.warning(self, "No Data", "The clipboard is empty.")
            return

        rows = text.split("\n")
        clean_rows = [row.strip() for row in rows if row.strip()]

        if not clean_rows:
            QMessageBox.warning(self, "Invalid Data", "No valid data found in clipboard.")
            return

        data = []

        for row in clean_rows:
            columns = row.split("\t")
            non_empty_columns = [col for col in columns if col.strip()]

            if len(non_empty_columns) >= 2:
                data.append(non_empty_columns)

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
                background_color = QColor('whitesmoke') if row_index % 2 == 0 else QColor('white')
                self.data_table.item(row_index, col_index).setBackground(background_color)

        self.data_table.resizeColumnsToContents()
        self.data_table.horizontalHeader().setSectionsMovable(True)

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
    def data_table_values_check(self):

        for col in range(self.data_table.columnCount()):
            for row in range(self.data_table.rowCount()):
                item = self.data_table.item(row, col)
                if item is None or not self.is_numeric(item.text()):
                    return False
        return True

    #---------------------------------------------------------------------------------------------
    def data_table_check(self):

        if self.data_table.rowCount() == 0:
            msg = 'Error: No data to import'
            self.status_bar.showMessage(msg, 5000)
            return False

        if not self.data_table_headers_check():
            msg = 'Error: Headers are not text'
            self.status_bar.showMessage(msg, 5000)
            return False

        if not self.data_table_values_check():
            msg = 'Error: Values are not numeric'
            self.status_bar.showMessage(msg, 5000)
            return False

        return True

    #---------------------------------------------------------------------------------------------
    def import_series(self):

        if not self.data_table_check(): return

        index = [float(self.data_table.item(row, 0).text()) for row in range(self.data_table.rowCount())] 
        X = self.data_table.horizontalHeaderItem(0).text()

        for col in range(1, self.data_table.columnCount()):

            values = [float(self.data_table.item(row, col).text()) for row in range(self.data_table.rowCount())] 
            Y = self.data_table.horizontalHeaderItem(col).text()

            serie_Id =  generate_Id()
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
            self.add_item_tree_widget(None, serieDict)          # will be added on parent from current index
            #print(f"{X} / {Y}")

            msg = f'{X} / {Y} imported as serie {serie_Id}'
            self.status_bar.showMessage(msg, 2000)

    #---------------------------------------------------------------------------------------------
    def import_pointers(self):

        if not self.data_table_check(): return

        # column order may have been changed
        header = self.data_table.horizontalHeader()
        column_order = [header.logicalIndex(i) for i in range(self.data_table.columnCount())]

        index = [float(self.data_table.item(row, column_order[0]).text()) for row in range(self.data_table.rowCount())] 
        X1Name = self.data_table.horizontalHeaderItem(column_order[0]).text()
        values = [float(self.data_table.item(row, column_order[1]).text()) for row in range(self.data_table.rowCount())] 

        item_Id =  generate_Id()
        itemDict = {
            'Id': item_Id, 
            'Type': 'INTERPOLATION', 
            'X1Coords': index,
            'X2Coords': values,
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

