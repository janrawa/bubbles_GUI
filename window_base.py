from typing import Tuple, Union
from PyQt6.QtWidgets import (QMainWindow, QApplication, QGroupBox, QLabel,
                             QGridLayout, QWidget, QPushButton, QFileDialog,
                             QMessageBox, QDialogButtonBox, QDialog, QVBoxLayout,
                             QComboBox, QHBoxLayout, QLineEdit)

from PyQt6.QtGui import QAction, QIntValidator, QDoubleValidator
from PyQt6.QtCore import Qt, QTimer

from abc import abstractmethod
import sys

def showErrorMessageBox(error : Union[str, Exception], description : str = None, parent = None):
        """Show QMessageBox with error message and optional description.

        Args:
            error (Union[str, Exception]): error code to display
            description (str, optional): descritption of the error. Defaults to None.
        """
        if isinstance(error, Exception):
            try:
                error=str(error)
            except Exception as e:
                showErrorMessageBox(e, parent=parent)

        warning_dialog=QMessageBox(parent=parent)
        warning_dialog.setWindowTitle("Error!")
        warning_dialog.setText(error)
        warning_dialog.setDetailedText(description)
        warning_dialog.exec()

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

class SettingsDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updatedSettings = {}

        self.myLayout=QVBoxLayout()
        self.myLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # self.settingLineEdits = [
        #     ('volatage',        self.createSetting('Voltage [V]', 0.0, (0.0, 2.0))),
        #     ('frequency',       self.createSetting('Frequency [Hz]', 0.0, (0.0, 2.0))),
        #     ('peak_threshold',  self.createSetting('Peak detection threshold', 0.0, (0.0, 2.0))),
        # ]

        self.settingLineEdits = self.createSettings([
            {'name':'volatage',         'label':'Voltage [V]',              'default':1.0,      'range':(0.5, 2.0)},
            {'name':'frequency',        'label':'Frequency [Hz]',           'default':1.5e6,    'range':(1e6, 2e6)},
            {'name':'peak_threshold',   'label':'Peak detection threshold', 'default':1e3,      'range':(100., 10000.)},
        ])

        # self.settingLineEdits.append()
        # self.settingLineEdits.append()
        # self.settingLineEdits.append()

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setCenterButtons(True)

        buttonOk=self.buttonBox.addButton(QDialogButtonBox.StandardButton.Ok)
        buttonApply=self.buttonBox.addButton(QDialogButtonBox.StandardButton.Apply)
        buttonCancel=self.buttonBox.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        # if self.setSettings() is succesfull than self.close()
        buttonOk.clicked.connect(lambda:self.close() if self.recordUpdatedSettings() else None)
        buttonApply.clicked.connect(self.recordUpdatedSettings)
        buttonCancel.clicked.connect(self.close)
        
        self.myLayout.addWidget(self.buttonBox)
        self.setLayout(self.myLayout)
        # deletes refrence to self.myLayout
        del self.myLayout
    
    def recordUpdatedSettings(self) -> bool:
        """Checks

        Returns:
            bool: _description_
        """
        changedSettings = {}
        for name, lineEdit in self.settingLineEdits:
            if lineEdit.text() != "":
                if not lineEdit.hasAcceptableInput():
                    showErrorMessageBox('Invalid value!', f'Value set in {name} is invalid!')
                    return False
                changedSettings.update({name:lineEdit.text()})
        
        self.updatedSettings.update(changedSettings)
        print(self.updatedSettings)
        return True

    def createSettings(self, settings:list[dict]) -> tuple:
        layout=QGridLayout(self)
        row=0
        settingLineEdits=[]
        for setting in settings:
            settingLabel    = QLabel(setting['label'])
            settingLineEdit = QLineEdit()

            layout.addWidget(settingLabel, row, 0)
            layout.addWidget(settingLineEdit, row, 1)
            row += 1

            settingLineEdit.setPlaceholderText(str(setting['default']))
            settingLineEdit.setAlignment(Qt.AlignmentFlag.AlignRight)

            settingLineEdit.setValidator(self.createValidator(setting['default'], setting['range']))

            settingLineEdits.append((setting['name'], settingLineEdit))
        
        self.myLayout.addLayout(layout)
        return tuple(settingLineEdits)
            

    def createSetting(self, label:str, default:Union[int, float], range=None) -> QLineEdit:
            settingLabel    = QLabel(label)
            settingLineEdit = QLineEdit()
            settingLayout   = QHBoxLayout()

            settingLineEdit.setPlaceholderText(str(default))
            settingLineEdit.setAlignment(Qt.AlignmentFlag.AlignRight)

            settingLineEdit.setValidator(self.createValidator(default, range))
            
            settingLayout.addWidget(settingLabel)
            settingLayout.addWidget(settingLineEdit)
            
            self.myLayout.addLayout(settingLayout)

            return settingLineEdit
            
    @staticmethod
    def createValidator(default, range):
        if type(default) == int:
            validator = QIntValidator()
        elif type(default) == float:
            validator = QDoubleValidator()
            validator.setDecimals(3)
        else:
            return None
        
        if range != None:
            validator.setRange(*range)
            validator.setDecimals(3)
        
        return validator




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
        settings_action = QAction('&Settings', self)
        exit_action     = QAction('&Exit', self)
                
        # Connect triggers
        save_action.triggered.connect(self.saveFile)
        settings_action.triggered.connect(self.openSettings)
        exit_action.triggered.connect(self.close)  # Connect Exit to close the application

        menu_bar.addActions([save_action, settings_action, exit_action])

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
    
    def openSettings(self):
        settingsDialog=SettingsDialog(self)
        settingsDialog.show()

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
        """Calls showErrorMessageBox function.

        Args:
            error (Union[str, Exception]): error code to display
            description (str, optional): descritption of the error. Defaults to None.
        """
        showErrorMessageBox(error, description, self)

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