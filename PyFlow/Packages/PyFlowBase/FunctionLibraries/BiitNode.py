import json

from PyFlow.Core import NodeBase
from PyFlow.Core.NodeBase import NodePinsSuggestionsHelper
from PyFlow.Core.Common import StructureType
from PyFlow.Packages.PyFlowBase.Nodes import FLOW_CONTROL_COLOR
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitUtils import getPinTypeFromIoType, filePathTypes, getOutputFilePath

def constructor(self, name):
    tool = self.__class__.tool

    super(self.__class__, self).__init__(name)

    for input in tool.info.inputs:
        pinName = f'{input.name}Pin'
        setattr(self, pinName, self.createInputPin(input.description, getPinTypeFromIoType(input.type), input.default_value))
        if input.type in filePathTypes:
            getattr(self, pinName).setInputWidgetVariant("FilePathWidget")

    for output in tool.info.outputs:
        pinName = f'{output.name}Pin'
        setattr(self, pinName, self.createOutputPin(output.description, getPinTypeFromIoType(output.type), output.default_value))
        getattr(self, pinName).setData(getOutputFilePath(output, name))
    
    self.headerColor = FLOW_CONTROL_COLOR
    self.lib = 'BiitLib'

def compute(self, *args, **kwargs):
    tool = self.__class__.tool
    # data = self.outputPathPin.currentData()
    # self.outputPin.setData(data)
    print('compute', args, kwargs)
    
    listLength = 0
    for input in tool.info.inputs:
        pinName = f'{input.name}Pin'
        value = getattr(self, pinName).currentData()
        if type(value) is list:
            listLength = max(len(value), listLength)
    
    for output in tool.info.outputs:
        pinName = f'{output.name}Pin'
        value = getOutputFilePath(output, self.name) if listLength==0 else json.dumps([str(getOutputFilePath(output, self.name, i)) for i in range(listLength)])
        getattr(self, pinName).setData(value)

@classmethod
def description(cls): 
    return cls.tool.info.description

@classmethod
def pinTypeHints(cls):
    helper = NodePinsSuggestionsHelper()
    for input in cls.tool.info.inputs:
        helper.addInputDataType(getPinTypeFromIoType(input.type))
    for output in cls.tool.info.outputs:
        helper.addOutputDataType(getPinTypeFromIoType(output.type))
    helper.addInputStruct(StructureType.Single)
    helper.addOutputStruct(StructureType.Single)
    return helper

@classmethod
def category(cls):
    return '|'.join(cls.tool.info.categories)

def createNode(tool):
# Hide the version number for now, but it would be nice to add it later when there are multiple versions of the tool
    # toolId = f'{tool.info.id}_v{tool.info.version}'
    toolId = f'{tool.info.id}'
    toolClass = type(toolId, (NodeBase, ), dict( 
        tool = tool,
        __init__= constructor, 
        compute = compute, 
        description = description,
        pinTypeHints = pinTypeHints,
        category = category
    ))
    return toolClass