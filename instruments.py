from typing import Any
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


    def __setattr__(self, name: str, value: Any) -> None:
        match name:
            case 'amplitude':
                # make sure it's float
                if not isinstance(value, float):
                    try:
                        value = float(value)
                    except ValueError:
                        raise TypeError(f"Attribute '{name}' must be a float or convertible to float.")

                self.instr.write(f':source1:voltage:amplitude {value}')
                super().__setattr__(name, value)

            case 'state':
                # make sure it's bool
                if not isinstance(value, bool):
                    try:
                        value = bool(value)
                    except ValueError:
                        raise TypeError(f"Attribute '{name}' must be a bool or convertible to bool.")

                if value:
                    self.instr.write(f':output1:state on')
                else:
                    self.instr.write(f':output1:state off')
                
                super().__setattr__(name, value)
            
            case _:
                # default behaviour
                super().__setattr__(name, value)
    
    def __getattribute__(self, name: str) -> Any:
        match name:
            case 'frequency':
                self.frequency=self.instr.ask(f':source1:frequency?')
                super().__getattribute__(name)
            case 'instrument_name':
                self.instrument_name=self.instr.ask('*IDN?')
                super().__getattribute__(name)
            case _:
                return super().__getattribute__(name)

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

def calculate_peak_voltage(target_pressure):
    pass