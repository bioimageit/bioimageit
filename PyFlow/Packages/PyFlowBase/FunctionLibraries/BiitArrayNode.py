from pathlib import Path
import json
import pandas
from qtpy.QtCore import Signal

from PyFlow import PARAMETERS_PATH, OUTPUT_DATAFRAME_PATH
from PyFlow.Core.EvaluationEngine import EvaluationEngine
from PyFlow.Core.NodeBase import NodePinsSuggestionsHelper
from PyFlow.Core.GraphManager import GraphManagerSingleton
from PyFlow.Core.Common import StructureType, PinOptions
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitNodeBase import BiitNodeBase
from PyFlow.ThumbnailManagement.ThumbnailGenerator import ThumbnailGenerator
from send2trash import send2trash
from blinker import Signal

class BiitArrayNodeBase(BiitNodeBase):
    
    def __init__(self, name, pinStructureIn=StructureType.Single):
        super(BiitArrayNodeBase, self).__init__(name)
        self.parametersChanged = Signal(bool)
        self.inArray = self.createInputPin("in", "AnyPin", structure=pinStructureIn, constraint="1")
        self.inArray.enableOptions(PinOptions.AllowAny)
        self.inArray.onPinConnectedBiit.connect(self.onInputConnected) # Different from dataBeenSet since dataBeenSet is also called when createDataFrameFromFolder() (shortcut to create a dataFrame from the files in a folder) 
        self.inArray.onPinDisconnected.connect(self.onInputDisconnected)
        self.outArray = self.createOutputPin("out", "AnyPin", structure=StructureType.Single, constraint="1")
        self.outArray.disableOptions(PinOptions.ChangeTypeOnConnection)
        self.folderDataFramePath = None
        self.resetParameters = None
        self.initializeTool()
        self.initializeParameters()
        self.lib = 'BiitLib'
    
    def setupConnections(self):
        self.inArray.dataBeenSet.connect(self.dataBeenSet)
    
    def initializeTool(self):
        # self.tool = self.__class__.tool if hasattr(self.__class__, 'tool') else None
        # if self.tool is None: return
        # tool:
        #   inputs:  default_value, description, help, is_advanced, is_data, name, type, value, select_info: names:[], values:[], value, type
        #   outputs:
        #   id
        # toolInfo['inputs'].append({ key: value for key, value in input.__dict__.items() if key not in ['select_info']})
        return

    def initializeInput(self, input):
        # for BiitToolNodes, selectInfo.values is built with Munch with Munch(dict(names=names, values=values)), so it should be a list. 
        # But values has a special meaning in dict, so it is a function instead of a list.
        # So if selectInfo.values is a function: use selectInfo['values'] instead (which is indeed the value list we want)
        selectInfoValues = (input.select_info.values if isinstance(input.select_info.values, list) else input.select_info['values'])  if input.type == 'select' else None
        defaultValue = selectInfoValues[0] if input.type == 'select' and (input.default_value is None or input.default_value == '') else input.default_value
        return dict(type='value', columnName='', value=defaultValue, defaultValue=defaultValue, dataType=input.type, auto=input.auto if hasattr(input, 'auto') else False)

    def initializeOutput(self, output):
        return dict(value=output.default_value, 
                    defaultValue=output.default_value, 
                    type=output.type if hasattr(output, 'type') else None, 
                    extension=output.extension if hasattr(output, 'extension') else None,
                    help=output.help if hasattr(output, 'help') else None)

    def initializeParameters(self):
        tool = self.__class__.tool if hasattr(self.__class__, 'tool') else None
        inputs = {} if tool is None else { input.name: self.initializeInput(input) for input in tool.info.inputs }
        outputs = {} if tool is None else { output.name: self.initializeOutput(output) for output in tool.info.outputs }
        self.parameters = dict(inputs=inputs, outputs=outputs)
    
    def postCreate(self, jsonTemplate=None):
        super().postCreate(jsonTemplate)

        if 'parameters' in jsonTemplate:
            # Hanlde old fils where parameters had only inputs
            if 'inputs' not in jsonTemplate['parameters'] and 'outputs' not in jsonTemplate['parameters']:
                jsonTemplate['parameters'] = dict(inputs=jsonTemplate['parameters'], outputs={})
            
            for io in ['inputs', 'outputs']:
                
                # Instead of overwriting parameters by doing self.parameters = jsonTemplate['parameters']
                # set the values one by one to avoid troubles with the out-of-date workflows which do not have all the parameters for the node
                for parameterName, parameter in jsonTemplate['parameters'][io].items():
                    if parameterName not in self.parameters[io]:
                        print(f'Warning: parameter "{parameterName}" does not exist in node "{self.name}". This means the saved file is out of date and does not correspond to the new inputs outputs definition.')
                        continue
                    for key, value in parameter.items():
                        self.parameters[io][parameterName][key] = value
            
        if 'folderDataFramePath' in jsonTemplate and jsonTemplate['folderDataFramePath'] is not None:
            self.folderDataFramePath = jsonTemplate['folderDataFramePath']
            # if not Path(self.folderDataFramePath).exists():
            #     raise Exception(f'Warning: the node {self.name} should create its dataFrame from the folder {self.folderDataFramePath}, but it does not exist.')
            self.createDataFrameFromFolder(self.folderDataFramePath, False)
        
        if 'outputDataFramePath' in jsonTemplate and jsonTemplate['outputDataFramePath'] is not None:
            outputFolder = self.getOutputMetadataFolderPath()
            if Path(outputFolder / jsonTemplate['outputDataFramePath']).exists():
                self.setOutputAndClean(pandas.read_csv(outputFolder / jsonTemplate['outputDataFramePath'], index_col=0), False)
                if 'executed' in jsonTemplate:
                    self.executed = True
                    self.dirty = False
            else:
                self.executed = False
                self.dirty = True

        #     self.createDataFrameFromInputs()
        # Connect inArray.dataBeenSet only if the graph is already built, otherwise it will be connected once the graph is built in Graph.populateFromJson()
        if not self.graph().populating:
            self.inArray.dataBeenSet.connect(self.dataBeenSet)

    def parameterColumnExists(self, data, inputName):
        return isinstance(data, pandas.DataFrame) and self.parameters['inputs'][inputName]['columnName'] in data.columns

    # update the parameters['inputs'] from data (but do not overwrite parameters['inputs'] which are already column names):
    # for all inputs which are auto, set the corresponding parameter to the column name
    def setParametersFromDataframe(self, data, overwriteExistingColumns=False):
        # if len(data.columns) == 0: return
        n = len(data.columns)-1 if isinstance(data, pandas.DataFrame) else -1
        tool = self.__class__.tool
        for input in tool.info.inputs:
            # Overwrite parameter if overwriteExistingColumns or the column does not exist in the new dataframe
            if hasattr(input, 'auto') and input.auto and data is not None:
                if overwriteExistingColumns or self.parameters['inputs'][input.name]['type'] == 'columnName' and not self.parameterColumnExists(data, input.name):
                    self.parameters['inputs'][input.name]['type'] = 'columnName'
                    self.parameters['inputs'][input.name]['columnName'] = data.columns[max(0, n)]
                    n -= 1
            # If not auto and param is from unexisting column: reset param
            elif self.parameters['inputs'][input.name]['type'] == 'columnName' and not self.parameterColumnExists(data, input.name):
                self.parameters['inputs'][input.name]['type'] = 'value'
                self.parameters['inputs'][input.name]['columnName'] = self.parameters['inputs'][input.name]['defaultValue']

    
    # The input pin was plugged: reset parameters
    def onInputConnected(self, other):
        # Reset folderDataFramePath since it should be None when the input pin has a dataFrame, 
        # otherwise folderDataFramePath and the input dataFrame are in conlict when loading the graph file (the dataFrame is given from the input, then it is overriden with folderDataFramePath)
        # Do not reset overwrite existing columns when we are loading graph
        loadingGraph = self.graph().populating
        if not loadingGraph:
            self.setParametersFromDataframe(self.getCachedDataFrame(), True)
    
    # The input pin was unplugged: reset parameters and dataFrame
    def onInputDisconnected(self, pin=None):

        self.inArray.setData(None)
        self.setParametersFromDataframe(None, False)
        if self.folderDataFramePath is not None:
            self.createDataFrameFromFolder(self.folderDataFramePath)

    # The input pin was plugged (self.resetParameters=True) or parameters were changed in the properties GUI (self.resetParameters=False): 
    #    - set the node dirty & unexecuted, 
    #    - update what depends on the dataframe:
    #          - (deprecated) if data is None: recreate dataframe if not resetParameters
    #            if data is not None and resetParameters : update the parameters from data (but do not overwrite parameters which are already column names)
    #          - send parametersChanged to update the table view
    def dataBeenSet(self, pin=None):
        self.dirty = True
        self.setExecuted(False)
        data = self.inArray.currentData()
        data = data if isinstance(data, pandas.DataFrame) else None
        # if data is None and self.resetParameters: self.initializeParameters()
        # Set parameters from new input dataFrame
        # if data is not None: self.setParametersFromDataframe(data, self.resetParameters)
        self.setParametersFromDataframe(data, False)

        #  Once parameters are set, send changes to update the table view
        self.parametersChanged.send(data)

    def getCachedDataFrame(self):
        data = self.inArray.currentData()
        return data if isinstance(data, pandas.DataFrame) else None

    def getDataFrame(self):
        # data = self.inArray.currentData()
        # data = data if isinstance(data, pandas.DataFrame) else self.inArray.getData()
        # return data if isinstance(data, pandas.DataFrame) else None
        data = self.inArray.getData()
        return data if isinstance(data, pandas.DataFrame) else None
    
    def getPreviousNodes(self):
        if not self.inArray.hasConnections(): return None
        return [i.owningNode() for i in self.inArray.affected_by]
    
    def getPreviousNode(self):
        if not self.inArray.hasConnections(): return None
        return self.getPreviousNodes()[0]
    
    def updateColumnNames(self, pin, oldName, newName):
        data = pin.getData()
        if data is None: return
        columns = {}
        for column in data.columns:
            nodeName = column.split(':')[0]
            if nodeName == oldName:
                columns[column] = newName + ':' + column.split(':')[1]
        data.rename(columns=columns)
        pin.setData(data)

    def updateName(self, oldName, newName):
        # update column names in all downstream dataFrames
        self.updateColumnNames(self.inArray, oldName, newName)
        self.updateColumnNames(self.outArray, oldName, newName)
        nextNodes = EvaluationEngine()._impl.getForwardNextLayerNodes(self)
        for node in nextNodes:
            node.updateName(oldName, newName)

    def serialize(self):
        template = super(BiitArrayNodeBase, self).serialize()
        template['parameters'] = self.parameters.copy()
        template['folderDataFramePath'] = self.folderDataFramePath
        outputFolder = self.getOutputMetadataFolderPath()
        if Path(outputFolder / OUTPUT_DATAFRAME_PATH).exists():
            if self.executed:
                template['outputDataFramePath'] = OUTPUT_DATAFRAME_PATH
            else:
                Path(outputFolder / OUTPUT_DATAFRAME_PATH).unlink()
        return template
    
    def hasGeneratedData(self):
        dataFolder = self.getOutputDataFolderPath()
        metadataFolder = self.getOutputMetadataFolderPath()
        return dataFolder.exists() and len(list(dataFolder.iterdir())) > 0 or metadataFolder.exists() and len(list(metadataFolder.iterdir())) > 0
    
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
    
    def getColumnName(self, parameterName):
        return self.name + ': ' + parameterName
    
    def setOutputColumns(self, tool, data):
        # for outputName, output in self.parameters['outputs'].items():
        #     data[self.getColumnName(outputName)] = [getOutputFilePath(output['type'], self.name, i) for i in range(len(data))]
        raise NotImplementedError()

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
        if outputData is None: return
        for outputName, output in self.parameters['outputs'].items():
            if self.getColumnName(outputName) not in outputData.columns: continue # sometimes the output column is not defined, as in LabelStatistics ; since it is only used for the image format, and compute() is not called
            outputPath = outputData.at[index, self.getColumnName(outputName)]
            if isinstance(outputPath, Path):
                outputPath.parent.mkdir(exist_ok=True, parents=True)    
            args[outputName] = str(outputPath)
    
    def getParameter(self, name, row):
        if name not in self.parameters['inputs']: return None
        parameter = self.parameters['inputs'][name]
        return parameter['value'] if parameter['type'] == 'value' else row[parameter['columnName']] if row is not None and parameter['columnName'] in row else None
    
    def setBoolArg(self, args, name):
        args[name] = ''
    
    def getWorkflowPath(self):
        graphManager = GraphManagerSingleton().get()
        return Path(graphManager.workflowPath).resolve()
    
    def getWorkflowDataPath(self):
        return self.getWorkflowPath() / 'Data'
    
    def getWorkflowToolsPath(self):
        return self.getWorkflowPath() / 'Tools'
    
    def setArg(self, args, parameterName, parameter, parameterValue, index):
        if parameterValue is None: return
        if type(parameterValue) is bool and parameterValue:         # if parameter is a boolean: only set arg if true
            self.setBoolArg(args, parameterName)
        elif type(parameterValue) is not bool:                          # otherwise, set arg to parameter value
            arg = str( parameterValue )
            if parameter['dataType'] == 'path':
                arg = arg.replace('[index]', str(index)) if index is not None else arg
                arg = arg.replace('[node_folder]', str(self.getWorkflowDataPath() / self.name))
                arg = arg.replace('[workflow_folder]', str(self.getWorkflowDataPath()))
            args[parameterName] = arg
        return
    
    def parameterIsUndefinedAndRequired(self, parameterName, inputs, row=None):
        return any([toolInput.required and self.getParameter(parameterName, row) is None for toolInput in inputs if toolInput.name == parameterName])
    
    def getArgs(self):
        toolInfo = self.__class__.tool.info
        argsList = []
        inputData: pandas.DataFrame = self.inArray.currentData()
        outputData: pandas.DataFrame = self.outArray.currentData()
        if inputData is None:
            args = {}
            for parameterName, parameter in self.parameters['inputs'].items():
                if self.parameterIsUndefinedAndRequired(parameterName, toolInfo.inputs):
                    raise Exception(f'The parameter {parameterName} is undefined, but required.')
                self.setArg(args, parameterName, parameter, parameter['value'], None)
            # self.setOutputArgs(toolInfo, args)
            self.setOutputArgsFromDataFrame(toolInfo, args, outputData, 0)
            argsList.append(args)
            return argsList
        for index, row in inputData.iterrows():
            args = {}
            for parameterName, parameter in self.parameters['inputs'].items():
                if self.parameterIsUndefinedAndRequired(parameterName, toolInfo.inputs, row):
                    raise Exception(f'The parameter {parameterName} is undefined, but required.')
                if parameter['type'] == 'value':
                    self.setArg(args, parameterName, parameter, parameter['value'], index)
                else:
                    self.setArg(args, parameterName, parameter, row[parameter['columnName']], index)
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
        # argsList = argsList if type(argsList) is list else [argsList]

        outputFolder = self.getOutputDataFolderPath()
        if outputFolder.exists():
            send2trash(outputFolder)
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
        self.finishExecution(argsList)
        return True

    def finishExecution(self, argsList=None):
        argsList = self.getArgs() if argsList is None else argsList
        outputFolder = self.getOutputMetadataFolderPath()
        outputFolder.mkdir(exist_ok=True, parents=True)

        outputData: pandas.DataFrame = self.outArray.currentData()
        ThumbnailGenerator.get().generateThumbnails(self.name, outputData)

        if isinstance(outputData, pandas.DataFrame):
            outputData.to_csv(outputFolder / OUTPUT_DATAFRAME_PATH)
        
        if argsList is not None:
            with open(outputFolder / PARAMETERS_PATH, 'w') as f:
                json.dump(argsList, f)

        self.setExecuted(True)

    def createDataFrameFromInputs(self):
        tool = self.__class__.tool
        inputs = [i for i in tool.info.inputs] # if hasattr(i, 'auto') and i.auto]
        if len(inputs) == 0: return None
        data = pandas.DataFrame()
        for inputName, input in self.parameters['inputs'].items():
            data[self.getColumnName(inputName)] = [input['value']]
        ThumbnailGenerator.get().generateThumbnails(self.name, data)
        return data

    def createDataFrameFromFolder(self, path, initParameters=True):
        self.folderDataFramePath = path
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
        ThumbnailGenerator.get().generateThumbnails(self.name, data)
        if len(data)>0:
            # self.inArray.dataBeenSet.disconnect(self.dataBeenSet)
            self.inArray.setData(data)
            # self.inArray.dataBeenSet.connect(self.dataBeenSet)
            
            # Useful if self.inArray.dataBeenSet is not connected to self.dataBeenSet yet:
            self.setParametersFromDataframe(data, False)

    def clear(self):
        self.deleteFiles()
        super().clear()
    
    def deleteFiles(self):
        ThumbnailGenerator.get().deleteThumbnails(self.name)
        for outputFolder in [self.getOutputDataFolderPath(), self.getOutputMetadataFolderPath()]:
            if outputFolder.exists():
                send2trash(outputFolder)

    @classmethod
    def description(cls): 
        return cls.tool.info.help if hasattr(cls, 'tool') and hasattr(cls.tool, 'info') and hasattr(cls.tool.info, 'help') else ''

    @classmethod
    def category(cls):
        return '|'.join(cls.tool.info.categories)

def createNode(tool):
    # Hide the version number for now, but it would be nice to add it later when there are multiple versions of the tool
    # toolId = f'{tool.info.id}_v{tool.info.version}'
    # toolId = f'{tool.info.id}_biitarray'
    toolId = f'{tool.info.id}'
    toolClass = type(toolId, (BiitArrayNodeBase, ), dict(tool = tool))
    return toolClass

class SimpleITKBase(BiitArrayNodeBase):

    def __init__(self, name):
        super(SimpleITKBase, self).__init__(name)

    @staticmethod
    def category():
        return "SimpleITK"