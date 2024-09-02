from typing import Any
import usbtmc
from agilentMSO9404A import agilentMSO9404A
from numba import jit

class Scope(agilentMSO9404A):
    '''
    Initiates communication with agilentMSO9404A oscilloscope.
    '''
    def __init__(self, vendor_id=0x0957, product_id=0x900d):
        instrument = usbtmc.Instrument(vendor_id, product_id)
        self.instrument_name = instrument.ask('*IDN?')
        super().__init__(instrument)
    
    def fetch_data(self):
        '''
        Wrapper for fetch_waveform on channel 0(described as channel
        1 on phisical instrument).
        '''
        return self.channels[0].measurement.fetch_waveform()

class Generator(usbtmc.Instrument):
    def __init__(self, vendor_id=0x0699, product_id=0x0343):
        super().__init__(vendor_id, product_id)


    def __setattr__(self, name: str, value: Any) -> None:
        # specific procedures to do before setting variable
        match name:
            case 'amplitude':
                # make sure it's float
                if not isinstance(value, float):
                    try:
                        value = float(value)
                    except ValueError:
                        raise TypeError(f"Attribute '{name}' must be a float or convertible to float.")

                self.write(f':source1:voltage:amplitude {value}')
            case 'state':
                # make sure it's bool
                if not isinstance(value, bool):
                    try:
                        value = bool(value)
                    except ValueError:
                        raise TypeError(f"Attribute '{name}' must be a bool or convertible to bool.")

                if value:
                    self.write(':output1:state on')
                else:
                    self.write(':output1:state off')

        super().__setattr__(name, value)
    
    def __getattribute__(self, name: str) -> Any:
        # specific procedures to do before returning variable
        match name:
            case 'frequency':
                self.frequency=float(self.ask(':source1:frequency?'))
            case 'instrument_name':
                self.instrument_name=self.ask('*IDN?')
            case 'amplitude':
                self.amplitude=float(self.ask(':source1:voltage:amplitude?'))
            case 'state':
                self.state=True if self.ask(':output1:state?') == '1' else False
        
        return super().__getattribute__(name)

    def close(self):
        self.close()

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

def calculate_peak_voltage(target_pressure):
    pass