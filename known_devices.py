# set of known oscilloscope idVendor and idProduct
knownOscilloscopes = {
    ('0x957', '0x900d'), 
    ('0x957', '0x900b'),
}
# set of known generators idVendor and idProduct
knownGenerators = {
    ('0x699', '0x343'),
}

def device_type(device) -> str:
    ids = (hex(device.idVendor), hex(device.idProduct))

    if ids in knownOscilloscopes:
        return 'Osc'
    if ids in knownGenerators:
        return 'Gen'
    
    return 'UknDev'

def known_device_list() -> tuple:
    from usbtmc import list_devices
    devices=list_devices()

    return (
        devices,
        [
            f'{hex(dev.idVendor)}:{hex(dev.idProduct)} {device_type(dev)}' \
            for dev in devices
        ]
    )
