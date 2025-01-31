from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import pandas as pd

from .misc import *
from .CustomQTableWidget import CustomQTableWidget 

#=========================================================================================
class importSeriesWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, open_importWindow, add_item_tree_widget):
        super().__init__()

        self.open_importWindow = open_importWindow
        self.add_item_tree_widget = add_item_tree_widget

        title = 'Series importer'
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 800, 600)
        
        #----------------------------------------------
        data_layout = QVBoxLayout()
        self.data_table = CustomQTableWidget()
        self.data_table.setColumnCount(3)
        self.data_table.setRowCount(0)
        self.data_table.setHorizontalHeaderLabels(['X column', 'Y1 column', '(Y2 column)'])
        self.data_table.resizeColumnsToContents()

        data_layout.addWidget(self.data_table)

        #----------------------------------------------
        main_layout = QVBoxLayout()
        main_layout.addLayout(data_layout)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        self.import_button = QPushButton("Import series", self)
        self.clear_button = QPushButton("Clear table", self)
        self.close_button = QPushButton("Close", self)
        button_layout.addStretch()

        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.import_button.clicked.connect(self.import_series)
        self.clear_button.clicked.connect(self.clear_table)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

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
            QMessageBox.warning(self, "Invalid Data", "At least 2 columns (X,Y) or (X,Y1,Y2,...)")
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

    #---------------------------------------------------------------------------------------------
    def clear_table(self):
        
        self.data_table.setColumnCount(3)
        self.data_table.setRowCount(0)
        self.data_table.clearContents()
        self.data_table.setHorizontalHeaderLabels(['X column', 'Y1 column', '(Y2 column)'])
        self.data_table.resizeColumnsToContents()

    #---------------------------------------------------------------------------------------------
    def is_numeric(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    #---------------------------------------------------------------------------------------------
    def data_table_headers_check(self):
        header0 = self.data_table.horizontalHeaderItem(0).text()
        header1 = self.data_table.horizontalHeaderItem(1).text()

        if not self.is_numeric(header0) and not self.is_numeric(header1):
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
    def import_series(self):

        if self.data_table.rowCount() == 0:
            msg = 'No data to import'
            self.status_bar.showMessage(msg, 5000)
            return

        if not self.data_table_headers_check():
            msg = 'Headers are not text'
            self.status_bar.showMessage(msg, 5000)
            return

        if not self.data_table_values_check():
            msg = 'Values are not numeric'
            self.status_bar.showMessage(msg, 5000)
            return

        index = [float(self.data_table.item(row, 0).text()) for row in range(self.data_table.rowCount())] 
        X = self.data_table.horizontalHeaderItem(0).text()

        for col in range(1, self.data_table.columnCount()):
            values = [float(self.data_table.item(row, col).text()) for row in range(self.data_table.rowCount())] 
            Y = self.data_table.horizontalHeaderItem(col).text()
            serieDict = {
                'Id': generate_Id(), 
                'Type': 'Serie', 
                'Name': '', 
                'X': X,
                'Y': Y,
                'Y axis inverted': False,
                'Color': generate_color(),
                'History': 'Imported data',
                'Comment': '',
                'Serie': pd.Series(values, index=index),
                }
            self.add_item_tree_widget(None, serieDict)          # will be added on parent from current index
            #print(f"{X} / {Y}")

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

    importWindow = importSeriesWindow(open_importWindow, handle_item)
    open_importWindow[Id_importWindow] = importWindow
    importWindow.show()

    sys.exit(app.exec_())

