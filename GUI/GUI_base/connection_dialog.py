from typing import Tuple
from PyQt6.QtWidgets import (QLabel, QDialogButtonBox, QDialog, QVBoxLayout,
                             QComboBox)


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

class ConnectionOscilloscopeDialog(QDialog):
    def __init__(self, *args, item_list : Tuple[str]=('1','2','3','4', ), **kwargs):
        super().__init__(*args, **kwargs)

        QBtn = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QDialogButtonBox(QBtn)

        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.rejected.connect(self.close)

        layout          = QVBoxLayout()
        messageOsc      = QLabel("Select oscilloscope:")

        self.comboOsc   = QComboBox(self)
        self.comboOsc.addItems(item_list)

        layout.addWidget(messageOsc)
        layout.addWidget(self.comboOsc)
        
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
