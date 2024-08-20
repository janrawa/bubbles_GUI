import usbtmc
from agilentMSO9404A import agilentMSO9404A

class Scope(agilentMSO9404A):
    '''
    Initiates communication with agilentMSO9404A oscilloscope.
    '''
    def __init__(self, vendor_id=0x0957, product_id=0x900d):
        instr = usbtmc.Instrument(vendor_id, product_id)
        self.instrument_name = instr.ask('*IDN?')
        super().__init__(instr)
    
    def fetch_data(self):
        '''
        Wrapper for fetch_waveform on channel 0(described as channel
        1 on phisical instrument).
        '''
        return self.channels[0].measurement.fetch_waveform()

class Generator():
    def __init__(self) -> None:
        pass

    def set_peak_voltage(peak_voltage : float) -> None:
        pass