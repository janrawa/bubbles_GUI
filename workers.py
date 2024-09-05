from time import sleep
from typing import Any, Callable
from types import MethodType

from queue import Empty
from multiprocessing import Queue, Process, Event, Pipe

from instruments import Oscilloscope


class OscilloscopeProcessManager(Process):
    def __init__(self) -> None:
        super().__init__()
        self.daemon = True
        self.task_queue = Queue()
        self.data_queue = Queue()

        self.parent_pipe, self.child_pipe = Pipe()

        self.pause_event = Event()
        self.pause_event.set()
        self.stop_event  = Event()

        self.oscilloscope=None
    
    def __getattr__(self, name: str) -> Any:
        self.parent_pipe.send(name)
        
        while not self.stop_event.is_set():
            if self.parent_pipe.poll():
                return self.parent_pipe.recv()
            sleep(.01)
        
        raise BrokenPipeError('Process is not running, attributes cannot be accesed!')
    
    def run(self):
        self.oscilloscope=Oscilloscope()
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
            elif not self.pause_event.is_set() \
                    and self.oscilloscope.triggered:
                y=self.oscilloscope.fetch_y_data()
                self.data_queue.put(y)
                del y
            
            sleep(.01)
        self.oscilloscope.close()
    
    def pause(self):
        self.pause_event.set()
    
    def play(self):
        self.pause_event.clear()

    def stop(self):
        self.stop_event.set()
        self.join(timeout=2)

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
    """
    Short lasting processes that are run on rare ocations ex.
    saving gathered data to an archive file.
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