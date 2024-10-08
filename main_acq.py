#!/usr/bin/env python
from PyQt6.QtWidgets import QApplication
from GUI.main_window_acq import MainWindow

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    # Define the style sheet
    style_sheet = """
        * {
            font-size: 12pt;
        }
    """

    # Apply the style sheet to the application
    app.setStyleSheet(style_sheet)

    main = MainWindow()
    main.show()
    sys.exit(app.exec())