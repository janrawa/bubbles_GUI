import usbtmc
from ivi.agilent import agilentMSO9404A

class Intrument(agilentMSO9404A):
    def __init__(self, vendor_id=0x0957, product_id=0x900d):
        instr = usbtmc.Instrument(vendor_id, product_id)
        self.instrument_name = instr.ask('*IDN?')
        super().__init__(instr)
    
    def fetch_data(self):
        return self.channels[0].measurement.fetch_waveform()