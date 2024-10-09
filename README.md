# Bubbles GUI Readme
## Introduction
GUI for automatic generator voltage tunning based on oscilloscope (Agilent Technologies MSO9404A) readout.

## How to use
1. Connect devices to PC.
2. Setup devices as describen in [Configuring udev](#configuring_udev).
3. Startup the program.
4. Click either 'Connect' button.
5. Select devices.
    - If you encounter issues with this step try running script as root (not recomended).
6. After establishing connection buttons have new functions:
    - Button in 'Generator' panel toggles voltage tuner
    - Button in 'Oscilloscope' panel toggles data acquisistion.
7. (Optional) Save recorded data using save in toolbar menu.
8. Exit

## Benchmarking
The are limitations on transfer speeds beetween Oscilloscope and PC. Transfer time is an exponential function. Mostly linear below 200k samples.

![Plot with points and fitted polynomial](Benchmark.png)

Benchmarking was performed on computer with AMD Ryzen 7 3700X 8-Core Processor, so resoults may vary based on that. Record length is a quantity of points in a single acquisition.


## <a name="configuring_udev"></a>Configuring udev
If you cannot access your device without running your script as root follow the link: [Python USBTMC Readme](http://alexforencich.com/wiki/en/python-usbtmc/readme)
or are running it on Windows (untested).

### In case of issues try this
https://stackoverflow.com/questions/50625363/usberror-errno-13-access-denied-insufficient-permissions

1. **Replace 'idVendor' and 'idProduct' with values** and run line to create usb- udev file:
```console
sudo echo -e '# USBTMC instruments
# Agilent MSO7104
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="idVendor", ATTRS{idProduct}=="idProduct", GROUP="usbtmc", MODE="0666"
# Tektronix AFG3102
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="idVendor", ATTRS{idProduct}=="idProduct", GROUP="usbtmc", MODE="0660"
# Devices
KERNEL=="usbtmc/*",       MODE="0660", GROUP="usbtmc"
KERNEL=="usbtmc[0-9]*",   MODE="0660", GROUP="usbtmc"' >> /etc/udev/rules.d/usbtmc.rules
```
where the vendor and product ID must go in hex and without the "0x" **or add products of a given vendor by omiting ATTRS{idProduct} part of rule definition**. 

2. Refresh udev

```console
sudo udevadm control --reload-rules && sudo udevadm trigger
```

3. <span style="color: red;">Disconnect and re-connect the USB device.</span>

## Environment setup
It is advised to use [pyenv](https://github.com/pyenv/pyenv) or equivalent.

1. clone repository: `git clone https://github.com/janrawa/bubbles_GUI.git`
2. (Install Python build dependencies)[https://github.com/pyenv/pyenv/wiki#suggested-build-environment]
3. Install Python 3.11.9: `pyenv install 3.11.9`
4. Inside bubbles_GUI directory set local environment: `pyenv local 3.11.9`
5. Install dependencies: `pip install -r requirements.txt`


## Dependencies
Python 3.11.9
* PyQt6>=6.7.1
* python_usbtmc>=0.8
* pyusb>=1.2.1
* numpy>=2.1.1
* scipy>=1.14.1
### OS
#### Linux based OS is necessary due to shared memory between processes not working on windows
