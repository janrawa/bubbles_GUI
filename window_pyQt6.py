from tempfile import NamedTemporaryFile, TemporaryDirectory

from known_devices import known_device_list
from window_base import ConnectionDialog, MainWindowBase
from instruments import Generator
from workers import DeviceManagerProcess
from save_file import append_binary_file, write_archive_xy

from usbtmc import list_devices

from concurrent.futures import ProcessPoolExecutor

from decimal import Decimal
def float_to_eng(number:float, digits:int=4):
    return Decimal(round(number, digits)).normalize().to_eng_string()

class MainWindow(MainWindowBase):
    def __init__(self):
        super().__init__()
        self.tempDataDir        = TemporaryDirectory()
        self.tempDataFile       = NamedTemporaryFile(dir=self.tempDataDir.name, delete=False)
        self.tempDataAcquired   = False


        self.deviceManager  = None

        self.generatorGroupBox.connectionButton.clicked.connect(
            self.changeGeneratorState
        )
        self.oscilloscopeGroupBox.connectionButton.clicked.connect(
            self.changeOscilloscopeState
        )

        self.poolExecutor = ProcessPoolExecutor(max_workers=1)

    def initDevices(self, deviceOsc, deviceGen):
        self.deviceManager = DeviceManagerProcess(deviceOsc, deviceGen, autostart=True)

        # Fetch generator name
        generatorName=self.deviceManager.gen__getattr__('instrument_name')
        # Fetch generator state
        generatorState=self.deviceManager.gen__getattr__('state')

        self.generatorGroupBox.updateWidgets(
            instrument_name=generatorName,
            state=generatorState
        )
        
        self.generatorGroupBox.connectionButton.updateLabels(
            generatorState
        )


        # Fetch oscilloscope name
        self.oscilloscopeGroupBox.updateWidgets(
            instrument_name=self.deviceManager.osc__getattr__('instrument_name')
        )
        # Fetch acquisition state
        self.oscilloscopeGroupBox.connectionButton.updateLabels(
            not self.deviceManager.pause_event.is_set()
        )

    def connectDevicesDialog(self):
        # get device
        device_list, str_items=known_device_list()
        dialog=ConnectionDialog(self,
            item_list=str_items
        )

        dialog.buttonBox.accepted.connect(
            lambda: self.initDevices(
                device_list[dialog.comboOsc.currentIndex()] if len(device_list) else None,
                device_list[dialog.comboGen.currentIndex()] if len(device_list) else None
            )
        )
        
        dialog.exec()

    def changeGeneratorState(self):
        """Button logic for generatorGroupBox.connectionButton. Connects
        device/starts/stops generator output in apropriete circumstances.
        """
        if self.deviceManager == None:
            self.connectDevicesDialog()

        if self.deviceManager != None:
            # Fetch generator state
            newGeneratorState = not self.deviceManager.gen__getattr__('state')
            self.deviceManager.gen__setattr__('state', newGeneratorState)
            
            self.generatorGroupBox.connectionButton.updateLabels(
                newGeneratorState
            )
            self.generatorGroupBox.updateWidgets(
                state=newGeneratorState
            )


    def changeOscilloscopeState(self):
        """Button logic for oscilloscopeGroupBox.connectionButton. Connects
        device/starts/stops acquisition in apropriete circumstances.
        """
        
        if self.deviceManager == None:
            self.connectDevicesDialog()
        
        if self.deviceManager != None:
            self.oscilloscopeGroupBox.connectionButton.updateLabels(
                not self.deviceManager.pause_event.is_set()
            )

            # Update sample rate
            self.oscilloscopeGroupBox.updateWidgets(
                acquisition_state=not self.deviceManager.pause_event.is_set(),
                sample_rate=float_to_eng(self.deviceManager.osc__getattr__('analog_sample_rate'))
            )

            self.deviceManager.togglePause()

    def updateWidgets(self):
        """Updates widget display Generator and Oscilloscope (if connected).
        Some display values are slow to fetch from deviced like
        `analog_sample_rate`, so they're not updated every frame.
        """
        if self.deviceManager != None:
            self.generatorGroupBox.updateWidgets(
                frequency=float_to_eng(self.deviceManager.gen__getattr__('frequency')),
                amplitude=round(self.deviceManager.gen__getattr__('amplitude'), 4)
            )
        
    def performBackgroundTasks(self):
        """Perform background tasks:
            * save acquired data to binary file,
            * <add more later>
        """
        if self.deviceManager != None:
            while not self.deviceManager.data_queue.empty():
                y=self.deviceManager.data_queue.get()
                self.tempDataAcquired = True

                append_binary_file(self.tempDataFile.name, y)
                
                

    def saveFile(self):
        """Perform neccesary checks and save acquired data to archive.
        """
        if not self.tempDataAcquired:
            self.showErrorMessageBox(
                'No data to save!', 'Try performing acquisitioin and saving.'
            )
            return
        
        if self.deviceManager.pause_event.is_set():
            self.showErrorMessageBox(
                'Acquisition running!', 'Try stoping acquisitioin and saving.'
            )
            return
        
        if not self.deviceManager.data_queue.empty():
            self.showErrorMessageBox(
                'Data in queue!', ('Try waiting a while.'
                                   ' Data in queue waiting to be processed:'
                                   f' {self.deviceManager.data_queue.qsize()}.')
            )
            return
        
        path = super().saveFile()

        if path:
            metadata = {}
            if self.deviceManager != None:
                metadata['scope'] = {
                    'scope_name'    : self.deviceManager.osc__getattr__('instrument_name'),
                    'sample_rate'   : self.deviceManager.osc__getattr__('analog_sample_rate'),
                    'record_length' : self.deviceManager.osc__getattr__('record_length'),
                }
                metadata['generator'] = {
                    'generator_name': self.deviceManager.gen__getattr__('instrument_name'),
                    'frequency'     : self.deviceManager.gen__getattr__('frequency'),
                    'amplitude'     : self.deviceManager.gen__getattr__('amplitude')
                }

            # write_archive process wrapper; keeps tempDataFile from beeing deleted
            # before creating an archive
            self.poolExecutor.submit(write_archive_xy, metadata,
                                     self.deviceManager.osc_call_method('fetch_x_data'),
                                     self.tempDataFile.name, path)
            self.tempDataFile = NamedTemporaryFile(dir=self.tempDataDir.name, delete=False)
            self.tempDataAcquired = False

    def close(self):
        """Application window will close, than all the devices and processes.
        """
        super().close()
        self.poolExecutor.shutdown(wait=True)

        if self.deviceManager != None:
            self.deviceManager.stop()