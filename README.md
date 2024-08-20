# Bubbles GUI Readme
## Introduction
GUI for automatic generator voltage tunning based on oscilloscope (Agilent Technologies MSO9404A) readout.
Program is designed to be simple and modifiable in case the instruments change.
If you need to connect diffrent device feel free to edit `instrument.py` file.

## Configuring udev
If you cannot access your device without running your script as root follow the link: [Python USBTMC Readme](http://alexforencich.com/wiki/en/python-usbtmc/readme)
or are running it on Windows (untested).

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
