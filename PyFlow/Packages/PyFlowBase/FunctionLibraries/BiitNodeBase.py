from blinker import Signal
from PyFlow.Core import NodeBase
from PyFlow.Core.EvaluationEngine import EvaluationEngine
from PyFlow.invoke_in_main import inmain

class BiitNodeBase(NodeBase):

    log = Signal()

    def __init__(self, name):
        super().__init__(name)
        self.outputMessage = None               # The message which will be displayed in the Table View
        self.executed = None
        self.executedChanged = Signal(bool)
    
    def setPinDataAndClean(self, pin, data):
        pin.setData(data)
        pin.setClean()

    def setOutputAndClean(self, data):
        if not hasattr(self, 'outArray'): return
        # Set dirty to False before calling outArray.setData(data) since this can recompute
        self.dirty = False
        self.outArray.setData(data)
        self.outArray.setClean()

    def setExecuted(self, executed=True, propagate=True):
        if self.executed == executed: return
        self.executed = executed
        inmain(lambda: self.executedChanged.send(executed))
        # Propagate to following nodes is execution was unset?
        if propagate and not executed:
            nextNodes = EvaluationEngine()._impl.getEvaluationOrderIterative(self, forward=True)
            for node in [node for node in nextNodes if node != self]:
                node.setExecuted(False, propagate=False)

    def clear(self):
        self.setExecuted(False)