from types import MethodType
from pathlib import Path

from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase
from PyFlow.Core.PyCodeCompiler import Py3CodeCompiler

class ScriptNode(BiitArrayNodeBase):
    # input.name, input.type, input.description, input.default_value
    # tool = DefaultMunch.fromDict(dict(info=dict(inputs=[dict(name="ScriptPath", type="path", description="Script path", default_value="")])))
    def __init__(self, name):
        super(ScriptNode, self).__init__(name)
        # self.pathPin = self.createInputPin("Script path", "StringPin")
        # self.pathPin.setInputWidgetVariant("FilePathWidget")
        # self.pathPin.dataBeenSet.connect(self.scriptPathChanged)
        self.scriptPath = None

    def postCreate(self, jsonTemplate=None):
        super().postCreate(jsonTemplate)
        if 'scriptPath' in jsonTemplate:
            self.scriptPath = jsonTemplate['scriptPath']
            self.scriptPathChanged(self.scriptPath)

    def serialize(self):
        template = super(BiitArrayNodeBase, self).serialize()
        template['scriptPath'] = str(self.scriptPath)
        return template
    
    def dataBeenSet(self, pin=None, resetParameters=True):
        return
    def createDataFrameFromInputs(self):
        return
    def createDataFrameFromFolder(self, path):
        return
    def clear(self):
        return
    def compute(self, *args, **kwargs):
        return
    def execute(self):
        return
    
    def scriptPathChanged(self, path):
        self.scriptPath = path
        if not Path(path).exists():
            print(f'Warning: script path {path} does not exist for node {self.name}!')
            return
        with open(path, "r") as f:
            codeString = f.read()
            mem = Py3CodeCompiler().compile(codeString, self.getName(), {})

            if "compute" in mem:
                computeFunction = mem["compute"]

                def nodeCompute(*args, **kwargs):
                    computeFunction(self)

                self.compute = MethodType(nodeCompute, self)

            if "execute" in mem:
                executeFunction = mem["execute"]

                def nodeExecute(*args, **kwargs):
                    executeFunction(self)

                self.execute = MethodType(nodeExecute, self)
    
    def executeScript(self):
        if self.scriptPath is not None and Path(self.scriptPath).exists():
            self.processNode(True)
        else:
            raise Exception(f'Script path {self.scriptPath} does not exist.')

    @staticmethod
    def category():
        return "Scripts"