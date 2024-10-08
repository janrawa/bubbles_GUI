from PyQt6.QtWidgets import (QGroupBox, QLabel, QGridLayout)
from PyQt6.QtCore import Qt

from .connection_button import ConnectionButton

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
