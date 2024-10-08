from PyQt6.QtWidgets import QApplication
from window_base import MainWindowBase


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

    main = MainWindowBase()
    main.show()
    sys.exit(app.exec())