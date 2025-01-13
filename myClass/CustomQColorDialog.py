from PyQt5.QtWidgets import QColorDialog, QApplication
from PyQt5.QtGui import QColor
from matplotlib import cm

#=========================================================================================
class CustomQColorDialog:
    @staticmethod
    def getColor():
        # Create an instance of QColorDialog
        color_dialog = QColorDialog()
        color_dialog.setOption(QColorDialog.DontUseNativeDialog)

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

    # Call our custom class to get a color
    selected_color = CustomQColorDialog.getColor()
    if selected_color:
        print(f"Selected color: {selected_color.name()}")
    else:
        print("No color was selected.")

