from pathlib import Path
import json
import pandas
from qtpy.QtCore import Signal

from PyFlow.Core import NodeBase
from PyFlow.Core.NodeBase import NodePinsSuggestionsHelper
from PyFlow.Core.Common import StructureType, PinOptions
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitNodeBase import BiitNodeBase
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitUtils import getOutputFilePath, getOutputFolderPath, isIoPath
from PyFlow.Packages.PyFlowBase.Tools.ThumbnailGenerator import thumbnailGenerator

from blinker import Signal

class BiitArrayNodeBase(BiitNodeBase):

    def __init__(self, name):
        super(BiitArrayNodeBase, self).__init__(name)
        self.parametersChanged = Signal(bool)
        self.inArray = self.createInputPin("in", "AnyPin", structure=StructureType.Single, constraint="1")
        self.inArray.enableOptions(PinOptions.AllowAny)
        self.inArray.dataBeenSet.connect(self.dataBeenSet)
        self.inArray.onPinDisconnected.connect(self.dataBeenUnset)
        self.outArray = self.createOutputPin("out", "AnyPin", structure=StructureType.Single, constraint="1")
        self.outArray.disableOptions(PinOptions.ChangeTypeOnConnection)
        self.dataFramePath = None
        self.initializeTool()
        self.initializeParameters()
        self.lib = 'BiitLib'
    
    def initializeTool(self):
        # self.tool = self.__class__.tool if hasattr(self.__class__, 'tool') else None
        # if self.tool is None: return
        # tool:
        #   inputs:  default_value, description, help, is_advanced, is_data, name, type, value, select_info: names:[], values:[], value, type
        #   outputs:
        #   id
        # toolInfo['inputs'].append({ key: value for key, value in input.__dict__.items() if key not in ['select_info']})
        return

    def initializeParameters(self):
        tool = self.__class__.tool if hasattr(self.__class__, 'tool') else None
        self.parameters = {} if tool is None else { input.name: self.initializeInput(input) for input in tool.info.inputs }
    
    def initializeInput(self, input):
        defaultValue = input.select_info.values[0] if input.type == 'select' and (input.default_value is None or input.default_value == '') else input.default_value
        return dict(type='value', columnName='', value=defaultValue, dataType=input.type)

    def postCreate(self, jsonTemplate=None):
        super().postCreate(jsonTemplate)
        if 'parameters' in jsonTemplate:
            self.parameters = jsonTemplate['parameters']
        self.setExecuted(False)
        
        if 'dataFramePath' in jsonTemplate and jsonTemplate['dataFramePath'] is not None:
            self.dataFramePath = jsonTemplate['dataFramePath']
            self.createDataFrameFromFolder(self.dataFramePath, False)
        # else:
        #     self.createDataFrameFromInputs()

    # update the parameters from data (but do not overwrite parameters which are already column names):
    # for all inputs which are path, set the corresponding parameter to the column name
    def setParametersFromDataframe(self, data, overwriteExistingColumns=False):
        if len(data.columns) == 0: return
        n = len(data.columns)-1
        tool = self.__class__.tool
        for input in tool.info.inputs:
            if isIoPath(input) and (overwriteExistingColumns or self.parameters[input.name]['type'] == 'value'):
                self.parameters[input.name]['type'] = 'columnName'
                self.parameters[input.name]['columnName'] = data.columns[max(0, n)]
                n -= 1
        
    # The input pin was plugged (resetParameters=True) or parameters were changed in the properties GUI (resetParameters=False): 
    #    - set the node dirty, 
    #    - unexecuted, 
    #    - and update what depends on the dataframe:
    #          - (deprecated) if data is None: recreate dataframe if not resetParameters
    #            if data is not None and resetParameters : update the parameters from data (but do not overwrite parameters which are already column names)
    #          - send parametersChanged to update the table view
    def dataBeenSet(self, pin=None, resetParameters=True):
        self.dirty = True
        self.setExecuted(False)
        data = self.getDataFrame()
        if data is None and resetParameters: self.initializeParameters()
        # Set parameters from new input dataFrame
        # if data is not None and resetParameters: self.setParametersFromDataframe(data, False)
        if data is not None and resetParameters: self.setParametersFromDataframe(data, True)
        #  Once parameters are set, send change
        self.parametersChanged.send(data)
    
    # The input pin was unplugged: reset dataFrame
    def dataBeenUnset(self, pin=None):
        self.inArray.setData(None)

    def getDataFrame(self):
        data = self.inArray.currentData()
        data = data if isinstance(data, pandas.DataFrame) else self.inArray.getData()
        return data if isinstance(data, pandas.DataFrame) else None
    
    def getPreviousNodes(self):
        if not self.inArray.hasConnections(): return None
        return [i.owningNode() for i in self.inArray.affected_by]
    
    def getPreviousNode(self):
        if not self.inArray.hasConnections(): return None
        return self.getPreviousNodes()[0]
    
    def serialize(self):
        template = super(BiitArrayNodeBase, self).serialize()
        template['parameters'] = self.parameters.copy()
        template['dataFramePath'] = self.dataFramePath
        return template
    
    @staticmethod
    def pinTypeHints():
        helper = NodePinsSuggestionsHelper()
        helper.addInputDataType("AnyPin")
        helper.addOutputDataType("AnyPin")
        helper.addInputStruct(StructureType.Single)
        helper.addOutputStruct(StructureType.Single)
        return helper
    
    @staticmethod
    def category():
        return ""
    
    def getColumnName(self, output):
        return self.name + '_' + output.name
    
    def setOutputColumns(self, tool, data):
        for output in tool.info.outputs:
            data[self.getColumnName(output)] = [getOutputFilePath(output, self.name, i) for i in range(len(data))]

    def compute(self, *args, **kwargs):
        if not self.dirty: return
        data = self.getDataFrame()
        tool = self.__class__.tool
        if not isinstance(data, pandas.DataFrame): 
            data = self.createDataFrameFromInputs()
            if data is None: return
        data = data.copy()
        self.setOutputColumns(tool, data)
        self.dirty = False
        self.setOutputAndClean(data)
        return data
    
    # def setOutputArgs(self, toolInfo, args):
    #     for output in toolInfo.outputs:
    #         outputPath = getOutputFilePath(output, self.name)
    #         if isinstance(outputPath, Path):
    #             outputPath.parent.mkdir(exist_ok=True, parents=True)
    #         args[output.name] = str(outputPath)

    def setOutputArgsFromDataFrame(self, toolInfo, args, outputData, index):
        for output in toolInfo.outputs:
            outputPath = outputData.at[index, self.getColumnName(output)]
            if isinstance(outputPath, Path):
                outputPath.parent.mkdir(exist_ok=True, parents=True)    
            args[output.name] = str(outputPath)
    
    def setArg(self, args, parameterName, parameterValue):
        if type(parameterValue) is bool and parameterValue:         # if parameter is a boolean: only set arg if true
            args[parameterName] = ''
        elif type(parameterValue) is not bool:                          # otherwise, set arg to parameter value
            args[parameterName] = str( parameterValue )
        return
    
    def getArgs(self):
        toolInfo = self.__class__.tool.info
        argsList = []
        inputData: pandas.DataFrame = self.inArray.currentData()
        outputData: pandas.DataFrame = self.outArray.currentData()
        if inputData is None:
            args = {}
            for parameterName, parameter in self.parameters.items():
                self.setArg(args, parameterName, parameter['value'])
            # self.setOutputArgs(toolInfo, args)
            self.setOutputArgsFromDataFrame(toolInfo, args, outputData, 0)
            argsList.append(args)
            return argsList
        for index, row in inputData.iterrows():
            args = {}
            for parameterName, parameter in self.parameters.items():
                if parameter['type'] == 'value':
                    self.setArg(args, parameterName, parameter['value'])
                else:
                    self.setArg(args, parameterName, row[parameter['columnName']])
            self.setOutputArgsFromDataFrame(toolInfo, args, outputData, index)
            argsList.append(args)
        # else:
        #     argsList = RunTool.getInputArgs(toolInfo, self)
        #     RunTool.setOutputArgs(toolInfo, self, argsList)
        return argsList

    def execute(self, req, logTool):
        toolInfo = self.__class__.tool.info
        tool = req.get_tool(f'{toolInfo.id}_v{toolInfo.version}')

        argsList = self.getArgs()
        argsList = argsList if type(argsList) is list else [argsList]

        outputData: pandas.DataFrame = self.outArray.currentData()
        outputFolder = getOutputFolderPath(self.name)
        outputFolder.mkdir(exist_ok=True, parents=True)
        
        job_id = req.new_job()
        try:
            req.runner_service.set_up(tool, job_id)
            # for args in argsList:
            #     preparedArgs = req._prepare_command(tool, args)
            #     req.runner_service.exec(tool, preparedArgs, job_id)
            #     # req.exec(tool, **args)
            preparedArgs = [req._prepare_command(tool, args) for args in argsList]
            req.runner_service.exec_multi(tool, preparedArgs, job_id, outputFolder, logTool)
            req.runner_service.tear_down(tool, job_id)
        except Exception as err:
            req.notify_error(str(err), job_id)

        if isinstance(outputData, pandas.DataFrame):
            outputData.to_csv(outputFolder / 'output_data_frame.csv')
        with open(outputFolder / 'parameters.json', 'w') as f:
            json.dump(argsList, f)

        self.setExecuted(True)

        return True

    def createDataFrameFromInputs(self):
        tool = self.__class__.tool
        pathInputs = [i for i in tool.info.inputs if isIoPath(i)]
        if len(pathInputs) == 0: return None
        data = pandas.DataFrame()
        for input in pathInputs:
            data[self.getColumnName(input)] = [self.parameters[input.name]['value']]
        thumbnailGenerator.generateThumbnails(self.name, data)
        return data

    def createDataFrameFromFolder(self, path, initParameters=True):
        self.dataFramePath = path
        data = pandas.DataFrame()
        columnName = f'{self.name}_path'
        if isinstance(path, str) and len(path)==0 or not Path(path).exists():
            self.inArray.setData(None)
            return
        # data.attrs = {'single_data': True}
        path = Path(path)
        data[columnName] = [p for p in sorted(list(path.iterdir())) if p.name != '.DS_Store'] if path.is_dir() else [path] if path.exists() else [None]
        if initParameters:
            # Now that we have a pandas frame as input: let's consider the parameters type as columnName and set parameters['columnName']
            self.setParametersFromDataframe(data, True)
        thumbnailGenerator.generateThumbnails(self.name, data)
        if len(data)>0:
            # self.inArray.dataBeenSet.disconnect(self.dataBeenSet)
            self.inArray.setData(data)
            # self.inArray.dataBeenSet.connect(self.dataBeenSet)

    def clear(self):
        self.deleteFiles()
        super().clear()
    
    def deleteFiles(self):
        self.processNode(True)
        tool = self.__class__.tool
        data = self.getDataFrame()
        for output in tool.info.outputs:
            for index, row in data.iterrows():
                outputPath = row[output.name]
                if isinstance(outputPath, Path) and outputPath.exists():
                    outputPath.unlink()

def constructor(self, name):
    super(self.__class__, self).__init__(name)

def compute(self, *args, **kwargs):
    return super(self.__class__, self).compute(**kwargs)
    
@classmethod
def description(cls): 
    return cls.tool.info.help

@classmethod
def category(cls):
    return '|'.join(cls.tool.info.categories)

def createNode(tool):
    # Hide the version number for now, but it would be nice to add it later when there are multiple versions of the tool
    # toolId = f'{tool.info.id}_v{tool.info.version}'
    # toolId = f'{tool.info.id}_biitarray'
    toolId = f'{tool.info.id}'
    toolClass = type(toolId, (BiitArrayNodeBase, ), dict( 
        tool = tool,
        __init__= constructor, 
        compute = compute, 
        description = description,
        category = category
    ))
    return toolClass

class SimpleITKBase(BiitArrayNodeBase):

    def __init__(self, name):
        super(SimpleITKBase, self).__init__(name)

    @staticmethod
    def category():
        return "SimpleITK"