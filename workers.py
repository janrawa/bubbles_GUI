from time import sleep
from typing import Any
from types import MethodType

from multiprocessing import Queue, Process, Event, Pipe

from instruments import Generator, Oscilloscope

class DeviceManagerProcess(Process):
    """
    Class handling oscilloscope and generator communication on separete thread.
    Attributes can be accesed from the main thread at any moment without
    causing issues.

    IMPORTANT FOR ANY FUTURE MAINTAINER:
        * If you want to add any other functionality to any device and use it with this class:
            1. Edit __getattr__ and/or __setattr__ methods of Oscilloscope and/or Generator
            2. Use appropriete methods:
                * Get values using:
                    - gen__getattr__
                    - osc__getattr__
                * Set values using"
                    - gen__setattr__
                    - osc__setattr__

        * If you want to, please rework this mess. I tried and wasted a whole bunch of time and patience.
        
        WARNING:
            !!! ANY PROGRAM CRASH WITHIN MAIN LOOP OF PROCESS HANDLED WITH THIS
            CLASS WILL COUSE UNDEFINED BEHAVIOUR !!!
                * IT WILL F UP YOUR SETUP.
                * IT WILL BREAK COMUNICATION WITH INSTRUMENTS.
                * PROGRAM RESTART WILL NOT HELP YOU.
            
            As of 24.09.2024 no real fixes exist.
            Sometimes even full restart of instrumentation won't help.
            Eventually after many restarts and wasted time it will un F itself.
    """
    def __init__(self, oscilloscopeDevice, generatorDevice=None, autostart=False) -> None:
        super().__init__()
        self.daemon = True
        self.data_queue = Queue()

        # pipes for communication with main thread
        # child pipes accesible only in child thread
        self.__parent_gen_attr, self.__child_gen_attr = Pipe()
        self.__parent_osc_attr, self.__child_osc_attr = Pipe()

        self.pause_event = Event()
        self.pause_event.set()
        self.stop_event  = Event()

        self.__osc = Oscilloscope(oscilloscopeDevice)
        self.__gen = Generator(generatorDevice)

        if autostart:
            self.start()

    # Those methods should be reworked into something more Pythonic
    # but for now are ok enough
    def gen__setattr__(self, name: str, value: Any) -> None:
        self.gen_call_method('__setattr__', name, value)
    def gen__getattr__(self, name) -> Any:
        return self.gen_call_method('__getattr__', name)
    
    def osc__setattr__(self, name: str, value: Any) -> None:
        self.osc_call_method('__setattr__', name, value)
    def osc__getattr__(self, name) -> Any:
        return self.osc_call_method('__getattr__', name)
    
    def osc_call_method(self, name, *args, timeout=2):
        if not self.is_alive():
            raise BrokenPipeError('Process is not running, attributes cannot be accesed!')
        
        if hasattr(self.__osc, name):
            self.__parent_osc_attr.send((name, *args))
        else:
            raise AttributeError('Oscilloscope attribute not found!')
        
        if not self.stop_event.is_set():
            if self.__parent_osc_attr.poll(timeout=timeout):
                return self.__parent_osc_attr.recv()
        
    def gen_call_method(self, name, *args, timeout=2):
        if not self.is_alive():
            raise BrokenPipeError('Process is not running, attributes cannot be accesed!')
        
        if hasattr(self.__gen, name):
            self.__parent_gen_attr.send((name, *args))
        else:
            raise AttributeError('Generator attribute not found!')

        if not self.stop_event.is_set():
            if self.__parent_gen_attr.poll(timeout=timeout):
                return self.__parent_gen_attr.recv()
        
    def run(self):
        """Main loop of manager process. All calls are performed sequentially
        in following order:
            1. generator calls
            2. oscilloscope calls
            3. y-data fetch
        """
        while not self.stop_event.is_set():
            # Poll generator attribute pipe
            if self.__child_gen_attr.poll():
                # Get method name and *args
                attr_name, *args=self.__child_gen_attr.recv()
                if hasattr(self.__gen, attr_name):
                    attr=getattr(self.__gen, attr_name)
                    if type(attr) == MethodType:
                        self.__child_gen_attr.send(attr(*args))
                    else:
                        self.__child_gen_attr.send(None)
            # Poll osciloscope attribute pipe
            elif self.__child_osc_attr.poll():
                # Get method name and *args
                attr_name, *args=self.__child_osc_attr.recv()
                if hasattr(self.__osc, attr_name):
                    attr=getattr(self.__osc, attr_name)
                    if type(attr) == MethodType:
                        self.__child_osc_attr.send(attr(*args))
                    else:
                        self.__child_osc_attr.send(None)
            # Perform data acquisition and put it on data_queue
            elif self.pause_event.is_set():
                if self.__osc.triggered:
                    y=self.__osc.fetch_y_data()
                    self.data_queue.put(y)
                    del y
            
            sleep(.001)

    def pause(self):
        """
        Pause acquisition of new waveforms from oscilloscope.
        """
        self.pause_event.set()
    
    def play(self):
        """
        Start acquisition of new waveforms from oscilloscope.
        """
        self.pause_event.clear()

    def togglePause(self):
        """Toggle state of `self.pause_event`. 
        """
        if self.pause_event.is_set():
            self.play()
        else:
            self.pause()

    def stop(self):
        """
        Stop process and exit gracefully.
        """
        self.stop_event.set()
        self.join(timeout=2)
        self.__osc.close()
        self.__gen.close()