# set of known oscilloscope idVendor and idProduct
knownOscilloscopes = {
    ('0x957', '0x900d'), 
}
# set of known generators idVendor and idProduct
knownGenerators = {
    ('0x699', '0x343'),
}

def device_type(device) -> str:
    ids = (hex(device.idVendor), hex(device.idProduct))

    if ids in knownOscilloscopes:
        return 'Oscilloscope'
    if ids in knownGenerators:
        return 'Generator'
    
    return 'Uknown device'