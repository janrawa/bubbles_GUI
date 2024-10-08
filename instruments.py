from typing import Any
from usbtmc import Instrument

from numpy import arange, frombuffer, int16

class Oscilloscope(Instrument):
    """Oscilloscope communication class for easy acces to x and y values displayed on the instrument.
    """
    def __init__(self, *args, channel=1, timeout=2, **kwargs):
        """Create new Oscilloscope object based on usbtmc.Intrument.
        All connection methods of usbtmc should work with Oscilloscope class.

        Args:
            timeout (int, optional): Communication timeout in seconds. Defaults to 2.
        """
        super().__init__(*args, **kwargs)    
        
        self.timeout = timeout
        self.write('*CLS')  # Clear the status
        self.write(':system:header off')
        self.write(':waveform:streaming ON')  # Enable waveform streaming
        self.write(':waveform:byteorder lsbfirst')
        self.write(':waveform:format word')  # Set waveform format to 16-bit word

        self.write(f":WAV:SOUR CHAN{channel}")  # Set the channel to read from

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
            case 'record_length':
                return int(self.ask(":WAV:POIN?"))
            case 'channel':
                return self.ask(f":WAV:SOUR?")

    def fetch_x_data(self):
        """Fetch X-axis data (time data) from the oscilloscope.

        Returns:
            numpy.ndarray: Numpy array of X-axis data (time values).
        """
        x_increment = float(self.ask(":WAV:XINC?"))
        x_origin = float(self.ask(":WAV:XOR?"))
        x_reference = float(self.ask(":WAV:XREF?"))

        # Get the number of points from the oscilloscope
        num_points = int(self.ask(":WAV:POIN?"))

        # Generate the time (X-axis) data array
        x_data = arange(num_points) * x_increment + x_origin - x_reference * x_increment
        return x_data

    def fetch_y_data(self):
        """Fetch Y-axis data (voltage data) from the oscilloscope for a specified channel.

        Returns:
            numpy.ndarray: Numpy array of Y-axis data (voltage values).
        """
        
        # Get Y data scaling parameters
        y_increment = float(self.ask(":WAV:YINC?"))
        y_origin = float(self.ask(":WAV:YOR?"))
        y_reference = float(self.ask(":WAV:YREF?"))

        # Request the waveform data
        self.write(":WAV:DATA?")
        raw_data = self.read_raw()  # Read raw data

        # Process the raw data
        header_size = 2  # Standard header size for 16-bit word data
        
        # Convert raw data to a numpy array of 16-bit unsigned integers
        y_data = frombuffer(raw_data[header_size:-1], dtype=int16)
        # y_data = np.frombuffer(raw_data, dtype=np.int16, header_size=2)

        # Scale the data to get the correct voltage values
        y_data = (y_data - y_reference) * y_increment + y_origin
        return y_data

class Generator(Instrument):
    """Initiates communication with tektronix AFG3102 generator.

    Args:
        Instrument (class): USBTMC instrument interface client

    Raises:
        TypeError: in __setattr__: Attribute 'amplitude' must be a float or convertible to float.
        TypeError: in __setattr__: Attribute 'state' must be a bool or convertible to bool.
    """
    def __init__(self, *args, timeout=2, output_channel : int=1, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.timeout = timeout
        self._output_channel=output_channel
        self.write('*CLS')  # Clear the status

    def __setattr__(self, name: str, value: Any) -> None:
        # specific procedures to do before setting variable
        match name:
            case 'amplitude':
                # make sure it's float
                if not isinstance(value, float):
                    try:
                        value = float(value)
                    except ValueError:
                        raise TypeError(f"Attribute 'amplitude' must be a float or convertible to float.")

                self.write(f':source{self._output_channel}:voltage:amplitude {value:.3f}')
            case 'state':
                # make sure it's bool
                if not isinstance(value, bool):
                    try:
                        value = bool(value)
                    except ValueError:
                        raise TypeError("Attribute 'state' must be a bool or convertible to bool.")

                if value:
                    self.write(f':output{self._output_channel}:state on')
                else:
                    self.write(f':output{self._output_channel}:state off')
        
        super().__setattr__(name, value)
    
    def __getattr__(self, name: str) -> Any:
        # specific procedures to do before returning variable
        match name:
            case 'instrument_name':
                return self.ask('*IDN?')
            case 'frequency':
                return float(self.ask(f':source{self._output_channel}:frequency?'))
            case 'amplitude':
                return float(self.ask(f':source{self._output_channel}:voltage:amplitude?'))
            case 'state':
                return True if self.ask(f':output{self._output_channel}:state?') == '1' else False

def calculate_peak_voltage(target_pressure):
    pass