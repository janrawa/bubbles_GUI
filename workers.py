from time import sleep
from typing import Any, Callable
from types import MethodType

from queue import Empty
from multiprocessing import Queue, Process, Event, Pipe

from instruments import Generator, Oscilloscope


class OscilloscopeProcessManager(Process):
    """
    Class designed for handling oscilloscope communication on separete thread.
    Attributes can be accesed from the main thread at any moment without
    causing issues.

    :param vendor_id: The vendor ID of the oscilloscope.
    :param product_id: The product ID of the oscilloscope.
    """
    def __init__(self, device=None, vendor_id=0x0957, product_id=0x900d, autostart=False) -> None:
        super().__init__()
        self.daemon = True
        self.task_queue = Queue()
        self.data_queue = Queue()

        self.parent_pipe, self.child_pipe = Pipe()

        self.pause_event = Event()
        self.pause_event.set()
        self.stop_event  = Event()

        self.oscilloscope=None

        if device != None:
            self.oscilloscope=Oscilloscope(device)
        else:
            self.oscilloscope=Oscilloscope(vendor_id, product_id)

        if autostart:
            self.start()
        
    
    def __getattr__(self, name: str) -> Any:
        if not self.is_alive():
            raise BrokenPipeError('Process is not running, attributes cannot be accesed!')
        
        self.parent_pipe.send(name)
        
        while not self.stop_event.is_set():
            if self.parent_pipe.poll():
                return self.parent_pipe.recv()
            sleep(.001)
    
    def run(self):
        while not self.stop_event.is_set():
            # Poll pipe to send __getattr__ values back
            if self.child_pipe.poll():
                attr_name=self.child_pipe.recv()
                if hasattr(self.oscilloscope, attr_name):
                    # Send the attribute value back to the parent process
                    attr=getattr(self.oscilloscope, attr_name)
                    if type(attr) == MethodType:
                        self.child_pipe.send(attr())
                    else:
                        self.child_pipe.send(attr)
                else:
                    self.child_pipe.send(None)
            # Perform misc task - like waiting
            elif not self.task_queue.empty():
                task = self.task_queue.get()
                task()
            # Perform data acquisition and put it on data_queue
            elif self.pause_event.is_set() \
                    and self.oscilloscope.triggered:
                y=self.oscilloscope.fetch_y_data()
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
        self.oscilloscope.close()

class DeviceManagerProcess(Process):
    """
    Class designed for handling oscilloscope and generator communication on separete thread.
    Attributes can be accesed from the main thread at any moment without
    causing issues.
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
        while not self.stop_event.is_set():
            # Poll oscilloscope attribute pipe
            if self.__child_gen_attr.poll():
                # Get method name and *args
                attr_name, *args=self.__child_gen_attr.recv()
                if hasattr(self.__gen, attr_name):
                    attr=getattr(self.__gen, attr_name)
                    if type(attr) == MethodType:
                        self.__child_gen_attr.send(attr(*args))
                    else:
                        self.__child_gen_attr.send(None)
            # Poll generator attribute pipe
            elif self.__child_osc_attr.poll():
                # Get method name and *args
                attr_name, *args=self.__child_osc_attr.recv()
                if hasattr(self.__osc, attr_name):
                    attr=getattr(self.__osc, attr_name)
                    if type(attr) == MethodType:
                        self.__child_osc_attr.send(attr(*args))
                    else:
                        self.__child_gen_attr.send(None)
            # Perform data acquisition and put it on data_queue
            elif self.pause_event.is_set() \
                    and self.__osc.triggered:
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




class WorkerProcess(Process):
    """
    Constantly running processes, that start and finish on rare ocations ex.
    begining data acquisition from an oscilloscope.
    """
    def __init__(self, target_function : Callable, *args, **kwargs):
        super().__init__()
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs
        self.stop_event = Event()

    def run(self):
        while not self.stop_event.is_set():
            # Execute the target function with arguments
            self.target_function(*self.args, **self.kwargs)

    def stop(self):
        self.stop_event.set()

class ConsumerProcess(Process):
    """Used for performing short lasting processes that are run without repetition saving gathered data to an archive file.
    """
    def __init__(self, start:bool):
        super().__init__()
        self.process_queue = Queue()
        self.stop_event = Event()

        if start:
            self.start()
    
    def run(self):
        while not self.stop_event.is_set():
            try:
                target_function, args, kwargs = self.process_queue \
                    .get(timeout=2)
            except Empty:
                continue
            
            # Execute the target function with arguments
            if target_function is not None:
                target_function(*args, **kwargs)
    
    def schedule_process(self, target : Callable, *args, **kwargs):
        self.process_queue.put((target, args, kwargs))

    def stop(self):
        self.stop_event.set()
        self.join(timeout=2)