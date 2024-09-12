from PyQt6.QtWidgets import (QMainWindow, QApplication, QGroupBox, QLabel,
                             QGridLayout, QWidget, QPushButton, QFileDialog,
                             QMessageBox)

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

import sys


class ConnectionButton(QPushButton):
    def __init__(self):
        super().__init__('Connect')
        self.deviceState    = True # will change to false on first click
    
    def updateLabels(self, device_state : bool) -> None:
        if device_state:
            self.setText('Stop')
        else:
            self.setText('Start')

class GeneratorGroupBox(QGroupBox):
    def __init__(self):
        super().__init__('Generator')

        instrument_nameLabel    = QLabel('Name')
        stateLabel              = QLabel('State')
        frequencyLabel          = QLabel('Frequency')
        amplitudeLabel          = QLabel('Amplitude')

        self.instrument_name    = QLabel('N/A')
        self.state              = QLabel('N/A')
        self.frequency          = QLabel('N/A')
        self.amplitude          = QLabel('N/A')

        self.connectionButton   = ConnectionButton()

        self.gridLayout = QGridLayout()

        self.gridLayout.addWidget(instrument_nameLabel, 0, 0)
        self.gridLayout.addWidget(stateLabel, 1, 0)
        self.gridLayout.addWidget(frequencyLabel, 2, 0)
        self.gridLayout.addWidget(amplitudeLabel, 3, 0)

        self.gridLayout.addWidget(self.instrument_name,  0, 1, alignment=Qt.AlignmentFlag.AlignRight)
        self.gridLayout.addWidget(self.state,            1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        self.gridLayout.addWidget(self.frequency,        2, 1, alignment=Qt.AlignmentFlag.AlignRight)
        self.gridLayout.addWidget(self.amplitude,        3, 1, alignment=Qt.AlignmentFlag.AlignRight)

        self.gridLayout.addWidget(self.connectionButton, 4, 0, 1, 2)

        self.setLayout(self.gridLayout)
    
    def updateWidgets(self, **kwargs):
        for key, value in kwargs.items():
            if not isinstance(value, str):
                try:
                    value = str(value)
                except ValueError:
                    raise TypeError("Attribute 'state' must be a bool or convertible to bool.")
            
            getattr(self, key).setText(value)


class OscilloscopeGroupBox(QGroupBox):
    def __init__(self):
        super().__init__('Oscilloscope')

        instrument_nameLabel    = QLabel('Name')
        acquisitionStateLabel   = QLabel('Acquisition state')
        sampleRateLabel         = QLabel('Sampling rate')

        self.instrument_name    = QLabel('N/A')
        self.acquisition_state  = QLabel('N/A')
        self.sample_rate        = QLabel('N/A')
        
        self.connectionButton   = ConnectionButton()

        self.gridLayout = QGridLayout()

        self.gridLayout.addWidget(instrument_nameLabel, 0, 0)
        self.gridLayout.addWidget(acquisitionStateLabel, 1, 0)
        self.gridLayout.addWidget(sampleRateLabel, 2, 0)

        self.gridLayout.addWidget(self.instrument_name,      0, 1, alignment=Qt.AlignmentFlag.AlignRight)
        self.gridLayout.addWidget(self.acquisition_state,    1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        self.gridLayout.addWidget(self.sample_rate,          2, 1, alignment=Qt.AlignmentFlag.AlignRight)

        self.gridLayout.addWidget(self.connectionButton, 4, 0, 1, 2)

        self.setLayout(self.gridLayout)

    def updateWidgets(self, **kwargs):
        for key, value in kwargs.items():
            if not isinstance(value, str):
                try:
                    value = str(value)
                except ValueError:
                    raise TypeError("Attribute 'state' must be a bool or convertible to bool.")
            
            getattr(self, key).setText(value)

class MainWindowBase(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('Bubbles GUI')

        self.createMenuBar()
        self.generatorGroupBox    = GeneratorGroupBox()
        self.oscilloscopeGroupBox = OscilloscopeGroupBox()
        
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.generatorGroupBox, 0, 0)
        mainLayout.addWidget(self.oscilloscopeGroupBox, 0, 1)

        centralWidget = QWidget(self)
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)
        
        self.createUpdateTimer()

    def createMenuBar(self):
        # Create the menu bar
        menu_bar = self.menuBar()

        # Create actions
        save_action     = QAction('&Save', self)
        exit_action     = QAction('&Exit', self)
                
        # Connect triggers
        save_action.triggered.connect(self.saveFile)
        exit_action.triggered.connect(self.close)  # Connect Exit to close the application

        menu_bar.addAction(save_action)
        menu_bar.addAction(exit_action)

    def createUpdateTimer(self):
        # Initialize counter
        self.frame_counter = 0

        # Set up a QTimer
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.updateWidgets)
        self.timer.timeout.connect(self.performBackgroundTasks)
        self.timer.start()  # Start the timer

    def saveFile(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Archive Files (*.zip);;All Files (*.*)")
        return file_path

    def updateWidgets(self):
        pass
    
    def performBackgroundTasks(self):
        pass

    def showErrorMessageBox(self, error : str, description : str = None):
        warning_dialog=QMessageBox(self)
        warning_dialog.setWindowTitle("Error!")
        warning_dialog.setText(error)
        warning_dialog.setDetailedText(description)
        warning_dialog.exec()

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