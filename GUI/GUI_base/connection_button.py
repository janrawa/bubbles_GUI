from PyQt6.QtWidgets import QPushButton


class ConnectionButton(QPushButton):
    def __init__(self):
        super().__init__('Connect')
        self.deviceState    = True # will change to false on first click
    
    def updateLabels(self, device_state : bool) -> None:
        if device_state:
            self.setText('Stop')
        else:
            self.setText('Start')