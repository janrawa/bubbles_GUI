from ivi.agilent.agilentBaseInfiniium import agilentBaseInfiniium

class agilent9000(agilentBaseInfiniium):
    "Agilent Infiniium 9000 series IVI oscilloscope driver"
    
    def __init__(self, *args, **kwargs):
        self.__dict__.setdefault('_instrument_id', '')
        
        super(agilent9000, self).__init__(*args, **kwargs)
        
        self._analog_channel_name = list()
        self._analog_channel_count = 4
        self._digital_channel_name = list()
        self._digital_channel_count = 16
        self._channel_count = self._analog_channel_count + self._digital_channel_count
        self._bandwidth = 4e9
        
        self._horizontal_divisions = 10
        self._vertical_divisions = 8
        
        self._identity_description = "Agilent Infiniium 9000 series IVI oscilloscope driver"
        self._identity_supported_instrument_models = ['MSO9404A',]
        
        self._init_channels()
