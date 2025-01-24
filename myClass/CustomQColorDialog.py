from PyQt5.QtWidgets import QColorDialog, QApplication
from PyQt5.QtGui import QColor
from matplotlib import cm

#=========================================================================================
class CustomQColorDialog:
    @staticmethod
    def getColor(start_color_html=None):
        # Create an instance of QColorDialog
        color_dialog = QColorDialog()
        color_dialog.setOption(QColorDialog.DontUseNativeDialog)

        # Convert HTML color to QColor and set as the starting color
        if start_color_html:
            start_color = QColor(start_color_html)
            if start_color.isValid():  # Ensure the color code is valid
                color_dialog.setCurrentColor(start_color)

        # Retrieve colors from Matplotlib's tab20 palette
        tab20_colors = [QColor(*(int(c * 255) for c in cm.tab20(i)[:3])) for i in range(20)]

        # Add custom colors to the dialog
        for i, color in enumerate(tab20_colors):
            color_dialog.setCustomColor(i, color)

        # Open the dialog and retrieve the selected color
        if color_dialog.exec_() == QColorDialog.Accepted:
            return color_dialog.currentColor()
        else:
            return None  # No color was selected

#=========================================================================================
if __name__ == "__main__":
    app = QApplication([])

    # Define a starting color in HTML format
    starting_color_html = "#45EA56"  # Example: greenish color

    selected_color = CustomQColorDialog.getColor(starting_color_html)
    if selected_color:
        print(f"Selected color: {selected_color.name()}")  # Outputs the selected color in HTML format
    else:
        print("No color was selected.")
