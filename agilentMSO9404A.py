from agilent9000 import agilent9000

class agilentMSO9404A(agilent9000):
    "Agilent Infiniium MSO9404A IVI oscilloscope driver"
    
    def __init__(self, *args, **kwargs):
        self.__dict__.setdefault('_instrument_id', 'MSO9404A')
        
        super(agilentMSO9404A, self).__init__(*args, **kwargs)
        
        self._analog_channel_count = 4
        self._digital_channel_count = 16
        self._channel_count = self._analog_channel_count + self._digital_channel_count
        self._bandwidth = 4e9
        
        self._init_channels()
    