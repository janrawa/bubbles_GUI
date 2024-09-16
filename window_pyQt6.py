from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import  QTimer

from tempfile import NamedTemporaryFile, TemporaryDirectory

from window_base import ConnectionDialog, MainWindowBase
from instruments import Generator
from workers import OscilloscopeProcessManager
from save_file import append_binary_file, write_archive

from usbtmc import list_devices

from concurrent.futures import ProcessPoolExecutor

import pdb

from decimal import Decimal
def float_to_eng(number:float, digits:int=4):
    return Decimal(round(number, digits)).normalize().to_eng_string()

class MainWindow(MainWindowBase):
    def __init__(self):
        super().__init__()
        self.tempDataDir        = TemporaryDirectory()
        self.tempDataFile       = NamedTemporaryFile(dir=self.tempDataDir.name, delete=False)
        self.tempDataAcquired   = False

        self.generator      = None
        self.oscilloscope   = None

        self.generatorGroupBox.connectionButton.clicked.connect(
            self.changeGeneratorState
        )
        self.oscilloscopeGroupBox.connectionButton.clicked.connect(
            self.changeOscilloscopeState
        )

        self.processPoolExecutor = ProcessPoolExecutor(max_workers=1)

    def initGenerator(self, device) -> bool:
        try:
            self.generator = Generator(device)
        except Exception as e:
            self.showErrorMessageBox(e, 'Generator initialization failed! '\
                                             'Try reconnectin device.')

    def changeGeneratorState(self):
        """Button logic for generatorGroupBox.connectionButton. Connects
        device/starts/stops generator output in apropriete circumstances.
        """
        if self.generator == None:
            # get device
            device_list = list_devices()
            dialog=ConnectionDialog(self,
                item_list=[f'{hex(dev.idVendor)}:{hex(dev.idProduct)}' for dev in device_list]
            )

            dialog.buttonBox.accepted.connect(
                lambda: self.initGenerator(
                    device_list[dialog.comboBox.currentIndex()]
                ) if len(device_list) else None
            )
            
            dialog.exec()

        if self.generator != None:
            self.generator.state = not self.generator.state
            self.generatorGroupBox.connectionButton.updateLabels(
                self.generator.state
            )

            self.generatorGroupBox.updateWidgets(
                instrument_name=self.generator.instrument_name
            )
    def initOscilloscope(self, device):
        try:
            self.oscilloscope = OscilloscopeProcessManager(device=device, autostart=True)
        except Exception as e:
            self.showErrorMessageBox(str(e), 'Oscilloscope initialization failed! '\
                                             'Try reconnectin device.')
            
    def changeOscilloscopeState(self):
        """Button logic for oscilloscopeGroupBox.connectionButton. Connects
        device/starts/stops acquisition in apropriete circumstances.
        """
        
        if self.oscilloscope == None:
            device_list = list_devices()
            dialog=ConnectionDialog(self,
                item_list=[f'{hex(dev.idVendor)}:{hex(dev.idProduct)}' for dev in device_list]
            )

            dialog.buttonBox.accepted.connect(
                lambda: self.initOscilloscope(
                    device_list[dialog.comboBox.currentIndex()]
                ) if len(device_list) else None
            )
            
            dialog.exec()
        
        if self.oscilloscope != None:
            self.oscilloscopeGroupBox.connectionButton.updateLabels(
                not self.oscilloscope.pause_event.is_set()
            )

            # After 100 ms update `analog_sample_rate` display label.
            # Prevents blocking UI
            self.oscilloscopeGroupBox.updateWidgets(
                instrument_name=self.oscilloscope.instrument_name,
                sample_rate=float_to_eng(self.oscilloscope.analog_sample_rate)
            )

            self.oscilloscope.togglePause()

    def updateWidgets(self):
        """Updates widget display Generator and Oscilloscope (if connected).
        Some display values are slow to fetch from deviced like
        `analog_sample_rate`, so they're not updated every frame.
        """
        if self.generator != None:
            self.generatorGroupBox.updateWidgets(
                state=self.generator.state,
                frequency=float_to_eng(self.generator.frequency),
                amplitude=round(self.generator.amplitude, 4)
            )
        
        if self.oscilloscope != None:
            self.oscilloscopeGroupBox.updateWidgets(
                acquisition_state=self.oscilloscope.pause_event.is_set(),
            )
    
    def performBackgroundTasks(self):
        """Perform background tasks:
            * save acquired data to binary file,
            * <add more later>
        """
        if self.oscilloscope != None:
            while not self.oscilloscope.data_queue.empty():
                y=self.oscilloscope.data_queue.get()
                append_binary_file(self.tempDataFile.name, y)
                self.tempDataAcquired = True
                

    def saveFile(self):
        """Perform neccesary checks and save acquired data to archive.
        """
        if not self.tempDataAcquired:
            self.showErrorMessageBox(
                'No data to save!', 'Try performing acquisitioin and saving.'
            )
            return
        
        if self.oscilloscope.pause_event.is_set():
            self.showErrorMessageBox(
                'Acquisition running!', 'Try stoping acquisitioin and saving.'
            )
            return
        
        path = super().saveFile()

        if path:
            metadata = {
                'scope' : {
                    'scope_name'    : str(self.oscilloscope.instrument_name),
                    'sample_rate'   : str(self.oscilloscope.analog_sample_rate),
                    'record_length' : str(self.oscilloscope.record_length),
                },
                'generator' : {
                    'generator_name': str(self.generator.instrument_name),
                    'frequency'     : str(self.generator.frequency),
                    'amplitude'     : str(self.genexrator.amplitude)
                },
            }

            # write_archive process wrapper; keeps tempDataFile from beeing deleted
            self.processPoolExecutor.submit(write_archive, metadata, self.tempDataFile.name, path)
            self.tempDataFile = NamedTemporaryFile(dir=self.tempDataDir.name, delete=False)
            self.tempDataAcquired = False

    def close(self):
        """Application window will close, than all the devices and processes.
        """
        self.timer.stop()
        
        self.processPoolExecutor.shutdown(wait=True)
        
        super().close()

        if self.generator != None:
            self.generator.close()

        if self.oscilloscope != None:
            self.oscilloscope.stop()
        
        

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