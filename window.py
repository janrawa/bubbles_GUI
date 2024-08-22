from multiprocessing import Queue
from tempfile import NamedTemporaryFile



from save_file import append_binary_file, write_archive

import tkinter as tk

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


from instruments import Generator, Scope
from workers import ConsumerProcess, WorkerProcess


import numpy as np

import time
from numba import jit
import samplerate


import sys
import pdb

class ForkedPdb(pdb.Pdb):
    """A Pdb subclass that may be used
    from a forked multiprocessing child

    """
    def interaction(self, *args, **kwargs):
        _stdin = sys.stdin
        try:
            sys.stdin = open('/dev/stdin')
            pdb.Pdb.interaction(self, *args, **kwargs)
        finally:
            sys.stdin = _stdin

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.createWidgets()

        self.master.title('Bubbles GUI')
        # properly dispose of window
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # connect instrument
        self.scope = Scope()
        # self.generator = Generator()
        # instrument name known only after setting connection
        self.ax_scope.set_title(self.scope.instrument_name)
        # setup data scope_queue for y-values of fetched waveforms
        self.scope_queue = Queue()


        # macine state dictgionary
        self.machine_state = {
            'first_acquisition' : True,     # will first acquisition be performed?
            'acquisition_on'    : False,    # is acquisition loop running?
            'generator_on'      : False,    # is the burst generator on?
        }

        # creates temporary file for storing raw data
        self.tmp_savefile = None
        self.metadata = {
            'scope' : {
                'scope_name'    : self.scope.instrument_name,
                'sample_rate'   : self.scope.acquisition.sample_rate,
                'record_length' : None
            },
            'generator' : {
                'generator_name': 'Not Implemented',
            },
            'descriptnion' : None
        }

        self.number_of_plot_points = 200000

        self.acquisition_process = None
        self.generator_process = None
        self.misc_process = ConsumerProcess(start=True)

        # [WIP]
        self.generator_time     = np.linspace(-20, 0, num=21, dtype=np.int32)
        self.generator_voltage  = 1.2*np.ones(21)
        
        
        self.update_cancel_name = None
        self.update()
        


    def createWidgets(self):
        self.init_figure()
        # menubar
        menu_bar=tk.Menu()
        self.master.configure(menu=menu_bar)

        file_bar = tk.Menu(menu_bar, tearoff=0)
        
        menu_bar.add_cascade(label='File',
                                        menu=file_bar)
        file_bar.add_command(label='Save to file',
                                         command=self.save_file)
        file_bar.add_separator()
        file_bar.add_command(label='Exit',
                                     command=self.on_closing)
        
        
        toggle_menu = tk.Menu(menu_bar, tearoff=0)
        
        menu_bar.add_cascade(label='Start/Stop',
                                  menu=toggle_menu)
        toggle_menu.add_checkbutton(label='Acquisition',
                                         command=self.toggle_acquisition)
        toggle_menu.add_checkbutton(label='Generator Autotuner',
                                         command=self.toggle_generator)
        
        
    def init_figure(self):
        """
        Initializes figure, converts it into canvas
        and does a preliminary draw().
        """
        fig    = plt.figure(figsize=(8,8))
        self.ax_scope, self.ax_gen = fig.subplots(nrows=2)
        self.line_scope,  = self.ax_scope.plot([],[],lw=.5, antialiased=False,
                                               rasterized=True)
        self.line_gen,  = self.ax_gen.plot([],[],lw=.5)
        
        self.ax_scope.set_xlabel('time [s]')
        self.ax_scope.set_ylabel('voltage [V]')

        self.ax_gen.set_xlabel('[WIP] time-$n$ [updates]')
        self.ax_gen.set_ylabel('peak voltage [V]')


        # figure to canvas conversion
        self.canvas = FigureCanvasTkAgg(fig,master=self.master)
        self.canvas.get_tk_widget().grid(row=0,column=1)
        self.canvas.draw()

    @staticmethod
    def acquire_data(scope, xy_queue):
        """
        Acquires data from oscilloscope,
        enqueues it for plotting and saves it to binary file.
        """
        scope.measurement.initiate()
        
        xy = np.array(scope.fetch_data())
        xy_queue.put(xy)

        del xy

    def plot(self):
        """
        Plots waveform data. This method is run only once as a first time plot.
        """
        xy = self.scope_queue.get(block=True)

        ratio = self.number_of_plot_points/len(xy[:,0])

        x = samplerate.resample(xy[:,0], ratio, 'sinc_best')
        y = samplerate.resample(xy[:,1], ratio, 'sinc_best')

        self.line_scope.set_xdata(x) # set x data
        self.line_scope.set_ydata(y) # set y data
        self.ax_scope.relim()  # Recompute the data limits
        self.ax_scope.autoscale_view()  # Rescale the view


        self.line_gen.set_xdata(self.generator_time) # set x data
        self.line_gen.set_ydata(self.generator_voltage) # set y data

        self.ax_gen.relim()  # Recompute the data limits
        self.ax_gen.autoscale_view()  # Rescale the view


        self.canvas.draw()
        self.machine_state['first_acquisition'] = False
        self.metadata['scope']['record_length'] = len(xy[:,1])
    
    def update(self):
        """
        Update loop-like function for plots.
        """
        
        if not self.scope_queue.empty():
            xy = self.scope_queue.get()

            self.misc_process.schedule_process(append_binary_file,
                                               self.tmp_savefile.name, xy[:, 1])
            
            if self.machine_state['generator_on']:
                self.update_voltage(xy)

            if self.machine_state['acquisition_on']:
                self.update_plot(xy)
            
            del xy

        # updates plot in the background every 200 ms at most 
        self.update_cancel_name = self.master.after(200, self.update)
    
    def update_voltage(self, xy):
        """
        Parameters:
            xy - oscilloscope readout
        Description:
            Adjcusts generator voltage based on oscilloscope readout.
        """
        @jit
        def calculate_voltage(voltatage_register, desired_voltage):
            delta_voltage = .25*abs(voltatage_register[-1]-desired_voltage)
            # takes all but the first element and adds a new one at the end
            for i in range(len(voltatage_register)-1):
                voltatage_register[i] = voltatage_register[i+1]
            voltatage_register[-1] = voltatage_register[-2] + delta_voltage
            return voltatage_register
        
        # [WIP]
        @jit
        def get_desired_voltage(xy):
            return 1.24

        self.generator_voltage = calculate_voltage(self.generator_voltage, get_desired_voltage(xy))
        # [WIP] send new voltage to generator
        time.sleep(1)

    def update_plot(self, xy):
        """
        Updates plot values from from scope_queue.
        After running sets up another update in 200 ms.
        """
        ratio = self.number_of_plot_points/len(xy[:,0])
        y = samplerate.resample(xy[:,1], ratio, 'sinc_best')

        self.line_scope.set_ydata(y)
        self.line_gen.set_ydata(self.generator_voltage)
        
        self.canvas.draw()
    
    def toggle_acquisition(self):
        """
        Toggle acquisistion of waveform data and start plotting.
        """
        # This read cannot be performed during the fetching
        # it is perfomred before changing the aquisition state to prevent
        # performing more than one instrument ask at the time.
        # 
        # Same applies to the file write function.

        if not self.machine_state['acquisition_on']:
            # updates metadata
            self.metadata['scope']['sample_rate'] = self.scope.acquisition \
                .sample_rate

            self.tmp_savefile = NamedTemporaryFile()
            self.acquisition_process =  WorkerProcess(
                self.acquire_data,
                self.scope, self.scope_queue
            )
            self.acquisition_process.start()
        else:
            self.acquisition_process.stop()
        
        self.machine_state['acquisition_on'] = not self.machine_state['acquisition_on']

        if self.machine_state['first_acquisition']:
            self.plot()
    
    def toggle_generator(self):
        """
        Toggle generator of burst and start plotting peak voltage.
        """
        self.machine_state['generator_on'] = not self.machine_state['generator_on']
        if self.machine_state['first_acquisition']:
            self.plot()
    
    def save_file(self):
        """
        Saving recorded data to a permament archive file.
        """
        if self.machine_state['acquisition_on']:
            tk.messagebox.showerror(
                title='Error',
                message='Stop acquisition before saving file.'
            )
            return
        
        if self.machine_state['first_acquisition']:
            tk.messagebox.showerror(
                title='Error',
                message='Perform acquisition before saving file.'
            )
            return

        # Open the save file dialog
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".zip",  # Default file extension
            filetypes=[("Archive files", "*.zip"), ("All files", "*.*")],  # File types filter
            title="Save File As"
        )
        
        # If a file path is selected
        if file_path:
            try:    
                self.misc_process.schedule_process(write_archive,
                        self.metadata, self.tmp_savefile.name, file_path, )

            except Exception as e:
                tk.messagebox.showerror(
                    title='Error',
                    message=f'{e}'
                )
                return

            # tk.messagebox.showinfo(title='File saved', message=f'File saved at {file_path}')
            
            

    def on_closing(self):
        """
        Function closing down the programm in controlled matter.
        Stopping the plot update function, data fetch worker,
        closing connection to the scope and quiting the programm.
        """
        if self.machine_state['acquisition_on']:
            self.toggle_acquisition()

        if self.machine_state['generator_on']:
            self.toggle_generator()
        
        try:
            self.master.after_cancel(self.update_cancel_name)
        except:
            pass
        
        self.master.quit()
        self.master.destroy()

        # Stop the worker thread
        self.misc_process.stop()

        # join workers
        # self.acquisition_process.join()
        self.misc_process.join()
        

        self.scope.close()


        # self.generator_thread.stop()
        # self.generator_thread.join()  # Wait for the thread to finish



        # self.generator.close()

