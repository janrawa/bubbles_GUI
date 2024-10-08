from typing import Tuple, Union
from PyQt6.QtWidgets import (QMainWindow, QApplication, QGroupBox, QLabel,
                             QGridLayout, QWidget, QPushButton, QFileDialog,
                             QMessageBox, QDialogButtonBox, QDialog, QVBoxLayout,
                             QComboBox)

from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer

from abc import abstractmethod
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

class ConnectionDialog(QDialog):
    def __init__(self, *args, item_list : Tuple[str]=('1','2','3','4', ), **kwargs):
        super().__init__(*args, **kwargs)

        QBtn = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QDialogButtonBox(QBtn)

        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.rejected.connect(self.close)

        layout          = QVBoxLayout()
        messageGen      = QLabel("Select generator:")
        messageOsc      = QLabel("Select oscilloscope:")

        self.comboGen   = QComboBox(self)
        self.comboOsc   = QComboBox(self)
        self.comboGen.addItems(item_list)
        self.comboOsc.addItems(item_list)

        layout.addWidget(messageGen)
        layout.addWidget(self.comboGen)
        
        layout.addWidget(messageOsc)
        layout.addWidget(self.comboOsc)
        
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

class GeneratorGroupBox(QGroupBox):
    def __init__(self):
        super().__init__('Generator')

        instrument_nameLabel    = QLabel('Name')
        stateLabel              = QLabel('Output state')
        frequencyLabel          = QLabel('Frequency')
        amplitudeLabel          = QLabel('Amplitude')

        self.instrument_name    = QLabel('N/A')
        self.state              = QLabel('N/A')
        self.frequency          = QLabel('N/A')
        self.amplitude          = QLabel('N/A')

        self.connectionButton   = ConnectionButton()

        self.gridLayout = QGridLayout()

        # Add name labels
        for indx, widget in enumerate([
            instrument_nameLabel,
            stateLabel,
            frequencyLabel,
            amplitudeLabel,
            ]):
            self.gridLayout.addWidget(widget, indx, 0)
        # Add value labels
        for indx, widget in enumerate([
            self.instrument_name,
            self.state,
            self.frequency,
            self.amplitude,
            ]):
            self.gridLayout.addWidget(widget,  indx, 1, alignment=Qt.AlignmentFlag.AlignRight)

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
        channelNumberLabel      = QLabel('Channel')
        acquisitionStateLabel   = QLabel('Acquisition state')
        sampleRateLabel         = QLabel('Sampling rate')

        self.instrument_name    = QLabel('N/A')
        self.channel            = QLabel('N/A')
        self.acquisition_state  = QLabel('N/A')
        self.sample_rate        = QLabel('N/A')
        
        self.connectionButton   = ConnectionButton()
        
        self.gridLayout = QGridLayout()

        # Add name labels
        for indx, widget in enumerate([
            instrument_nameLabel,
            channelNumberLabel,
            acquisitionStateLabel,
            sampleRateLabel,
            ]):
            self.gridLayout.addWidget(widget, indx, 0)
        # Add value labels
        for indx, widget in enumerate([
            self.instrument_name,
            self.channel,
            self.acquisition_state,
            self.sample_rate,
            ]):
            self.gridLayout.addWidget(widget, indx, 1, alignment=Qt.AlignmentFlag.AlignRight)

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
    """Base clas of MainWindow (creates all widgets and update abstraction).
    """
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
        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(1000)
        self.updateTimer.timeout.connect(self.updateWidgets)
        self.updateTimer.timeout.connect(self.performBackgroundTasks)
        self.updateTimer.start()

    def saveFile(self):
        """Opens QFileDialog asking for saveFile path

        Returns:
            str: path to saveFile (name included)
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File",
                                                    "", 
                                                    "Archive Files (*.zip)")
        if not file_path.endswith(".zip"):
            file_path += ".zip"
        
        return file_path

    @abstractmethod
    def updateWidgets(self):
        """Abstract method for updating widgets on a set interval
        using self.updateTimer.
        """
        pass
    
    @abstractmethod
    def performBackgroundTasks(self):
        """Abstract method for performing tasks in the background
        (ex. appending tempDataFile) on a set interval using self.updateTimer.
        """
        pass

    def showErrorMessageBox(self, error : Union[str, Exception], description : str = None):
        """Show QMessageBox with error message and optional description.

        Args:
            error (Union[str, Exception]): error code to display
            description (str, optional): descritption of the error. Defaults to None.
        """
        if isinstance(error, Exception):
            try:
                error=str(error)
            except Exception as e:
                self.showErrorMessageBox(e)

        warning_dialog=QMessageBox(self)
        warning_dialog.setWindowTitle("Error!")
        warning_dialog.setText(error)
        warning_dialog.setDetailedText(description)
        warning_dialog.exec()

    def showComboMessageBox(self, item_list=Tuple[str]):
        dialog=ConnectionDialog(self, item_list=item_list)
        dialog.setWindowTitle("Select device")
        dialog.exec()

    def close(self):
        self.updateTimer.stop()
        super().close()
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