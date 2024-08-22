import usbtmc
from agilentMSO9404A import agilentMSO9404A
from numba import jit

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

class Generator:
    def __init__(self, vendor_id=0x0699, product_id=0x0343):
        self.instr = usbtmc.Instrument(vendor_id, product_id)
        self.instrument_name = self.instr.ask('*IDN?')

    def set_peak_voltage(self, peak_voltage : float) -> None:
        self.instr.write(f':source1:voltage:amplitude {peak_voltage}')
    
    def close(self):
        self.instr.close()

from numpy import array
def fetch_enqueue_data(scope, xy_queue):
    """
    Acquires data from oscilloscope,
    enqueues it for plotting and saves it to binary file.
    """
    scope.measurement.initiate()
    
    xy = array(scope.fetch_data())
    xy_queue.put(xy)

    del xy

@jit
def peak_voltage(target_pressure):
    pass