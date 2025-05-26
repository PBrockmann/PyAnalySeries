from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor

#===================================================================================
class CustomQTableWidget(QTableWidget):
    """
    A QTableWidget subclass with advanced copy functionality,
    including range selection and full table copying.
    """
    def __init__(self):
        super().__init__()

    def set_italic_headers(self):
        # Horizontal header
        for col in range(self.columnCount()):
            item = self.horizontalHeaderItem(col)
            if item:
                font = item.font()
                font.setItalic(True)
                item.setFont(font)

        # Vertical header
        for row in range(self.rowCount()):
            item = self.verticalHeaderItem(row)
            if item is None:
                item = QTableWidgetItem(f'  {row + 1}  ')  # index 1-based
                self.setVerticalHeaderItem(row, item)
            else:
                item.setText(f'  {row + 1}  ')  # overwrite if already present
            font = item.font()
            font.setItalic(True)
            item.setFont(font)
            gray_brush = QBrush(QColor('gray'))
            item.setForeground(gray_brush)

    def keyPressEvent(self, event):
        """
        Handle key press events, particularly CTRL+c for copying.
        """
        if event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
            self.copy_to_clipboard()
        else:
            # Pass other events to the default handler
            super().keyPressEvent(event)
    
    def copy_to_clipboard(self):
        """
        Copies the selected range of cells or the entire table to the clipboard.
        """
        selected_ranges = self.selectedRanges()
        include_headers = False

        if selected_ranges:
            # Copy only the selected range of cells
            top_row = selected_ranges[0].topRow()
            bottom_row = selected_ranges[0].bottomRow()
            left_col = selected_ranges[0].leftColumn()
            right_col = selected_ranges[0].rightColumn()

            rows = range(top_row, bottom_row + 1)
            cols = range(left_col, right_col + 1)

            # Check if the user selected a column, row, or the entire table
            if top_row == 0 and bottom_row == self.rowCount() - 1:
                # Entire column(s) selected
                include_headers = True
            elif left_col == 0 and right_col == self.columnCount() - 1:
                # Entire row(s) selected
                include_headers = True
        else:
            # Copy the entire table
            rows = range(self.rowCount())
            cols = range(self.columnCount())
            include_headers = True
        
        data = self.extract_table_data(rows, cols, include_headers)
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(data))
    
    def extract_table_data(self, rows, cols, include_headers=False):
        """
        Extracts the data from the specified rows and columns of the table.
        Optionally includes headers for rows and columns.
        """
        data = []

        # Include column headers if requested
        if include_headers:
            header_row = [self.horizontalHeaderItem(col).text() if self.horizontalHeaderItem(col) else "" for col in cols]
            data.append("\t".join(header_row))
        
        # Extract data for each row
        for row in rows:
            row_data = []
            for col in cols:
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            data.append("\t".join(row_data))
        
        return data

#===================================================================================
# Example usage
if __name__ == "__main__":
    app = QApplication([])

    rows = 5
    cols = 6

    table = CustomQTableWidget()
    table.setRowCount(rows)
    table.setColumnCount(cols)

    table.resize(800, 600)

    table.setSelectionMode(QAbstractItemView.ExtendedSelection)
    table.setSelectionBehavior(QAbstractItemView.SelectItems)

    # Set default headers for demonstration
    table.setHorizontalHeaderLabels([f"Column {i}" for i in range(cols)])
    table.setVerticalHeaderLabels([f"Row {i}" for i in range(rows)])
        
    # Populate with sample data
    for row in range(rows):
        for col in range(cols):
            table.setItem(row, col, QTableWidgetItem(f"R{row}C{col}"))

    table.show()
    app.exec_()

