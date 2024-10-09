from blinker import Signal
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase

class DialogNode(BiitArrayNodeBase):

    def __init__(self, name):
        super(DialogNode, self).__init__(name)
        self.executeSignal = Signal()
    
    # def dataBeenSet(self, pin=None, resetParameters=True):
    #     return
    # def createDataFrameFromInputs(self):
    #     return
    # def createDataFrameFromFolder(self, path):
    #     return
    # def clear(self):
    #     return
    def compute(self, *args, **kwargs):
        data = self.getDataFrame()
        return data

    def execute(self, req):
        self.executeSignal.send()
        return self.setExecuted(True)
    
    @staticmethod
    def category():
        return "Dialog"