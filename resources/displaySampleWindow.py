from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys

from .misc import *
from .CustomQTableWidget import CustomQTableWidget

#=========================================================================================
class displaySampleWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_displayWindows, item):
        super().__init__()

        self.Id = Id
        self.open_displayWindows = open_displayWindows
        self.item = item

        self.sampleDict = self.item.data(0, Qt.UserRole)

        title = 'Display SAMPLE : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 600, 300)
        
        self.tabs = QTabWidget()
        
        #----------------------------------------------
        parameters_tab = QWidget()
        parameters_layout = QVBoxLayout()

        layout_s1 = QHBoxLayout()
        label_s1 = QLabel(f"{self.sampleDict['Parameters']}")
        layout_s1.addWidget(label_s1)
        layout_s1.addStretch()

        parameters_layout.addLayout(layout_s1)
        parameters_layout.addStretch()

        parameters_tab.setLayout(parameters_layout)
        self.tabs.addTab(parameters_tab, "Parameters")

        #----------------------------------------------
        if 'XCoords' in self.sampleDict.keys():

            data_tab = QWidget()
            data_layout = QVBoxLayout()
            data_table = CustomQTableWidget()
            data_table.setRowCount(len(self.sampleDict['XCoords']))
            data_table.setColumnCount(1)
            data_table.setHorizontalHeaderLabels(['X coordinates'])
            for i in range(len(self.sampleDict['XCoords'])):
                data_table.setItem(i, 0, QTableWidgetItem(str(f"{self.sampleDict['XCoords'][i]:.6f}")))
                background_color = QColor('white') if i % 2 == 0 else QColor('whitesmoke')
                data_table.item(i, 0).setBackground(background_color)
            data_table.resizeColumnsToContents()
            data_table.set_italic_headers()

            data_layout.addWidget(data_table)

            data_tab.setLayout(data_layout)
            self.tabs.addTab(data_tab, "X sampling coordinates")

        #----------------------------------------------
        info_tab = QWidget()
        info_layout = QVBoxLayout()

        self.textName = QLabel(f"Name : <b>{self.sampleDict['Name']}</b>")

        labelHistory = QLabel("History :")
        self.textHistory = QTextEdit()
        self.textHistory.setFixedHeight(self.textHistory.fontMetrics().lineSpacing() * 10)
        self.textHistory.setText(self.sampleDict['History'])
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
        self.textComment.setText(self.sampleDict['Comment'])

        info_layout.addWidget(self.textName)
        info_layout.addWidget(labelHistory)
        info_layout.addWidget(self.textHistory)
        info_layout.addWidget(labelComment)
        info_layout.addWidget(self.textComment)
        info_layout.addStretch()

        info_tab.setLayout(info_layout)
        self.tabs.addTab(info_tab, "Info")

        #----------------------------------------------
        self.tabs.setCurrentIndex(0)

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

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.sampleDict['Comment'] = self.textComment.toPlainText()
        self.item.setData(0, Qt.UserRole, self.sampleDict)
        self.open_displayWindows.pop(self.Id, None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(item):
        print('handle', item)
 
    app = QApplication([])

    itemDict = {
        'Id': 'abcd',
        'Name': 'A name',
        'Type': 'SAMPLE', 
        'Parameters': '5 ; linear',
        'XCoords': [3, 7, 8.3, 9.4, 10],
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }

    item = QTreeWidgetItem()
    item.setData(0, Qt.UserRole, itemDict)

    open_displayWindows = {}
    Id_displayWindow = '1234'
    displayWindow = displaySampleWindow(Id_displayWindow, open_displayWindows, item)
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app.exec_())
