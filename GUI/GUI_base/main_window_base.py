from typing import Tuple, Union
from PyQt6.QtWidgets import (QMainWindow, QGridLayout, QWidget,
                             QFileDialog, QMessageBox)

from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer

from abc import abstractmethod
from .generator_groupbox import GeneratorGroupBox
from .oscilloscope_groupbox import OscilloscopeGroupBox
from .connection_dialog import ConnectionDialog


class WindowBase(QMainWindow):
    """Base clas of MainWindowBase and MainWindowAcquisitionOnlyBase (creates all widgets and update abstractions).
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('Bubbles GUI')

        self.createMenuBar()
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
        if file_path and not file_path.endswith(".zip"):
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

class MainWindowBase(WindowBase):
    """Base clas of MainWindow.
    """
    def __init__(self):
        super().__init__()
        
        self.generatorGroupBox    = GeneratorGroupBox()
        self.oscilloscopeGroupBox = OscilloscopeGroupBox()
        
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.generatorGroupBox, 0, 0)
        mainLayout.addWidget(self.oscilloscopeGroupBox, 0, 1)

        centralWidget = QWidget(self)
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

class MainWindowAcquisitionOnlyBase(WindowBase):
    """Base clas of MainWindow.
    """
    def __init__(self):
        super().__init__()

        self.oscilloscopeGroupBox = OscilloscopeGroupBox()
        
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.oscilloscopeGroupBox, 0, 0)

        centralWidget = QWidget(self)
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)