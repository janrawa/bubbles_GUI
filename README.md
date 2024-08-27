# Bubbles GUI Readme
## Introduction
GUI for automatic generator voltage tunning based on oscilloscope (Agilent Technologies MSO9404A) readout.
Program is designed to be simple and modifiable in case the instruments change.
If you need to connect diffrent device feel free to edit `instrument.py` file.

## Configuring udev
If you cannot access your device without running your script as root follow the link: [Python USBTMC Readme](http://alexforencich.com/wiki/en/python-usbtmc/readme)
or are running it on Windows (untested).

### In case of issues try this
https://stackoverflow.com/questions/50625363/usberror-errno-13-access-denied-insufficient-permissions

1. Add line to udev file:
```sudo echo '# USBTMC instruments \
# Agilent MSO7104 \
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="0957", ATTRS{idProduct}=="900d", GROUP="usbtmc", MODE="0666" \
# Tektronix AFG3102 \
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="0699", ATTRS{idProduct}=="0343", GROUP="usbtmc", MODE="0660" \
# Devices \
KERNEL=="usbtmc/*",       MODE="0660", GROUP="usbtmc" \
KERNEL=="usbtmc[0-9]*",   MODE="0660", GROUP="usbtmc"' >> /etc/udev/rules.d/50-myusb.rules```
where the vendor and product ID must go in hex and without the 0x. For example lsusb in my case produced Bus 001 Device 042: ID c251:2201 Keil Software, Inc. LASER Driver IJS and so my vendor ID is c251 and product ID is 2201.

2. Refresh udev

```sudo udevadm control --reload-rules && sudo udevadm trigger```

3. Disconnect and re-connect the USB device.


## Using the programm
1. Turn oscilloscope on.
2. Turn generator on.
3. Make sure that both devices are plugged in to controller PC.
4. Run the script `python main.py`.

## Dependencies
* matplotlib==3.9.2
* numba==0.60.0
* numpy==2.1.0
* python_ivi==0.14.9
* python_usbtmc==0.8
* samplerate==0.2.1
