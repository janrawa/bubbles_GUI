from typing import Any
import usbtmc
from agilentMSO9404A import agilentMSO9404A

from numpy import arange, array, frombuffer, int16

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

class Oscilloscope(usbtmc.Instrument):
    def __init__(self, vendor_id=0x0957, product_id=0x900d, timeout=2):
        """
        Initialize the oscilloscope instrument.

        :param vendor_id: The vendor ID of the oscilloscope.
        :param product_id: The product ID of the oscilloscope.
        :param timeout: Communication timeout in seconds.
        """
        super().__init__(vendor_id, product_id)
        self.timeout = timeout
        self.write('*CLS')  # Clear the status
        self.write(':system:header off')
        self.write(':waveform:streaming ON')  # Enable waveform streaming
        self.write(':waveform:byteorder lsbfirst')
        self.write(':waveform:format word')  # Set waveform format to 16-bit word

    def __getattr__(self, name: str) -> Any:
        # specific procedures to do before returning variable
        match name:
            case 'instrument_name':
                return self.ask('*IDN?')
            case 'analog_sample_rate':
                return float(self.ask(':acquire:srate:analog?'))
            case 'digital_sample_rate':
                return float(self.ask(':acquire:srate:digital?'))
            case 'triggered':
                return bool(int(self.ask(':TER?')))

    def fetch_x_data(self):
        """
        Fetch X-axis data (time data) from the oscilloscope.

        :return: Numpy array of X-axis data (time points).
        """
        x_increment = float(self.ask(":WAV:XINC?"))
        x_origin = float(self.ask(":WAV:XOR?"))
        x_reference = float(self.ask(":WAV:XREF?"))

        # Get the number of points from the oscilloscope
        num_points = int(self.ask(":WAV:POIN?"))

        # Generate the time (X-axis) data array
        x_data = arange(num_points) * x_increment + x_origin - x_reference * x_increment
        return x_data

    def fetch_y_data(self, channel=1):
        """
        Fetch Y-axis data (voltage data) from the oscilloscope for a specified channel.

        :param channel: The channel number to fetch data from (default is 1).
        :return: Numpy array of Y-axis data (voltage points).
        """
        # Set the channel to read from
        self.write(f":WAV:SOUR CHAN{channel}")

        # Get Y data scaling parameters
        y_increment = float(self.ask(":WAV:YINC?"))
        y_origin = float(self.ask(":WAV:YOR?"))
        y_reference = float(self.ask(":WAV:YREF?"))

        # Get the number of points from the oscilloscope
        num_points = int(self.ask(":WAV:POIN?"))

        # Request the waveform data
        self.write(":WAV:DATA?")
        raw_data = self.read_raw()  # Read raw data

        # Process the raw data
        header_size = 2  # Standard header size for 16-bit word data
        data_size = len(raw_data) - header_size - 1
        if data_size != num_points * 2:  # 16-bit data means 2 bytes per point
            raise ValueError(f"Mismatch in data length: expected {num_points * 2}, got {data_size}")
        
        # Convert raw data to a numpy array of 16-bit unsigned integers
        y_data = frombuffer(raw_data[header_size:-1], dtype=int16)
        # y_data = np.frombuffer(raw_data, dtype=np.int16, header_size=2)

        # Scale the data to get the correct voltage values
        y_data = (y_data - y_reference) * y_increment + y_origin
        return y_data

class Generator(usbtmc.Instrument):
    '''
    Initiates communication with tektronix AFG3102 generator.
    All atributres are set for channel 1!
    set attributes:
        amplitude - sets the high level of output amplitude
        state - sets arbitrary function generator output
    get attributes:
        instrument_name
        frequency
        amplitude
        state
    '''
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
    
    def __getattr__(self, name: str) -> Any:
        # specific procedures to do before returning variable
        match name:
            case 'instrument_name':
                return self.ask('*IDN?')
            case 'frequency':
                return float(self.ask(':source1:frequency?'))
            case 'amplitude':
                return float(self.ask(':source1:voltage:amplitude?'))
            case 'state':
                return True if self.ask(':output1:state?') == '1' else False

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