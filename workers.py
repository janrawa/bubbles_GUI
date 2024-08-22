import multiprocessing
import queue
import threading
import time

class WorkerProcess(multiprocessing.Process):
    """
    Constantly running processes, that start and finish on rare ocations ex.
    begining data acquisition from an oscilloscope.
    """
    def __init__(self, target_function, *args, **kwargs):
        super().__init__()
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs
        self.stop_event = multiprocessing.Event()

    def run(self):
        while not self.stop_event.is_set():
            # Execute the target function with arguments
            self.target_function(*self.args, **self.kwargs)

    def stop(self):
        self.stop_event.set()

class ConsumerProcess(multiprocessing.Process):
    """
    Short lasting processes that are run on rare ocations ex.
    saving gathered data to an archive file.
    """
    def __init__(self, start):
        super().__init__()
        self.process_queue = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()

        if start:
            self.start()
    
    def run(self):
        while not self.stop_event.is_set():
            try:
                target_function, args, kwargs = self.process_queue \
                    .get(timeout=2)
            except queue.Empty:
                continue
            
            # Execute the target function with arguments
            if target_function is not None:
                target_function(*args, **kwargs)
    
    def schedule_process(self, target, *args, **kwargs):
        self.process_queue.put((target, args, kwargs))

    def stop(self):
        self.stop_event.set()