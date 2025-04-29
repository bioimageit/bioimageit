from enum import Enum
import traceback, sys
from qtpy.QtCore import Signal, Slot, QObject, QRunnable

# class Status(Enum):
# 	STOPPED = 1
# 	LAUNCHING = 2
# 	LAUNCHED = 3
# Taken from https://www.pythonguis.com/tutorials/multithreading-pyqt6-applications-qthreadpool/

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.status = 0

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            self.status = 1
            result = self.fn(*self.args, **self.kwargs)
        except:
            self.status = -2
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
            self.status = -2
        else:
            self.status = 2
            self.signals.result.emit(result)  # Return the result of the processing
            self.status = 3
        finally:
            self.status = 4
            self.signals.finished.emit()  # Done
            self.status = 5
