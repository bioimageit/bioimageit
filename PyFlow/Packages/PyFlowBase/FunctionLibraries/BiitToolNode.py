from pathlib import Path
import json
import re
import pandas
from munch import Munch
import logging
import subprocess

from PyFlow import PARAMETERS_PATH, OUTPUT_DATAFRAME_PATH
from PyFlow.invoke_in_main import inthread, inmain
from PyFlow.Core import NodeBase
from PyFlow.Core.EvaluationEngine import EvaluationEngine
from PyFlow.Core.NodeBase import NodePinsSuggestionsHelper
from PyFlow.Core.GraphManager import GraphManagerSingleton
from PyFlow.Core.Common import StructureType, PinOptions
from PyFlow.ToolManagement.EnvironmentManager import environmentManager, Environment, attachLogHandler
from PyFlow.ThumbnailManagement.ThumbnailGenerator import ThumbnailGenerator
from send2trash import send2trash
from blinker import Signal

# Node is set dirty when:
# - node is created (except when node is loaded from a file and executed: self.dirty = False)
# - input pin is plugged in or out (dataBeenSet)
# - an upstream node is computed (dataBeenSet)

# Node is computed when:
# - users clicks on the node
# - node is dirty and a downstream node is computed
# - parameters are changed ( dataBeenSet -> table view computes node)
# - user executes ( RunTool.execute(node) )
# - user export workflow: TODO!

# Parameters are initialized when node is computed

# getDataFrame() returns the cached dataFrame when not dirty, computes otherwise.

# PyFlow does not allow dependency cycles (upstream node whose input comes from a downstream node), see PyFlow.Core.Common.connectPins, canConnectPins & cycleCheck

class BiitToolNode(NodeBase):
	_packageName = "PyFlowBase"
	log = Signal()

	nInstanciatedNodes = 0
	environment: Environment = None

	def __init__(self, name):
		super().__init__(name)
		self.outputMessage = None               # The message which will be displayed in the Table View
		self.executed = None
		self.executedChanged = Signal(bool)
		self.tool = self.Tool()
		multipleInputs = hasattr(self.Tool, 'multipleInputs') and self.Tool.multipleInputs
		self.inArray = self.createInputPin("in", "AnyPin", structure=StructureType.Multi if multipleInputs else StructureType.Single, constraint="1")
		self.inArray.enableOptions(PinOptions.AllowAny)
		if multipleInputs:
			self.inArray.enableOptions(PinOptions.AllowMultipleConnections)
		self.outArray = self.createOutputPin("out", "AnyPin", structure=StructureType.Single, constraint="1")
		self.outArray.disableOptions(PinOptions.ChangeTypeOnConnection)
		self.resetParameters = None
		self.dataFrame = None
		self.initializeParameters()
		self.lib = 'BiitLib'
		self.__class__.nInstanciatedNodes += 1
	
	def getOutputDataFolderPath(self):
		return GraphManagerSingleton().get().getWorkflowPath() / 'Data' / self.name

	def getOutputMetadataFolderPath(self):
		return GraphManagerSingleton().get().getWorkflowPath() / 'Metadata' / self.name
	
	# affectOthers is always true, except when loading node in BiitToolNode.postCreate()
	def setOutputAndClean(self, data, affectOthers=True):
		self.dirty = False
		if not hasattr(self, 'outArray'): return
		self.outArray.setData(data, affectOthers)
		self.outArray.setClean()

	def setExecuted(self, executed=True, propagate=True, setDirty=True):
		if not executed and setDirty:
			self.dirty = True
			self.dataFrame = None
			if hasattr(self, 'outArray'):
				self.outArray.setDirty()
		if self.executed == executed: return
		self.executed = executed
		# Propagate to following nodes is execution was unset
		if propagate and not executed:
			nextNodes = EvaluationEngine()._impl.getForwardNextLayerNodes(self)
			for node in [node for node in nextNodes if node != self]:
				node.setExecuted(False, propagate=True, setDirty=setDirty)
	
	def setupConnections(self):
		self.inArray.dataBeenSet.connect(self.setNodeDirty)
	
	def initializeInput(self, input):
		defaultValue = input.get('default')
		defaultValue = input['choices'][0] if defaultValue is None and 'choices' in input and len(input['choices']) > 0 else defaultValue
		return dict(type='columnName' if input.get('autoColumn', False) else 'value', columnName=None, value=defaultValue, defaultValue=defaultValue, dataType=input['type'], advanced=input.get('advanced'))

	def initializeOutput(self, output):
		return dict(value=output.get('default'), 
					defaultValue=output.get('default'), 
					dataType=output['type'], 
					extension=output.get('extension'),
					editable=output.get('editable'),
					help=output.get('help'))

	def initializeParameters(self):
		inputs = { input['name']: self.initializeInput(input) for input in self.tool.inputs }
		outputs = { output['name']: self.initializeOutput(output) for output in self.tool.outputs }
		self.parameters = dict(inputs=inputs, outputs=outputs)
	
	def postCreate(self, jsonTemplate=None):
		super().postCreate(jsonTemplate)

		if 'executed' in jsonTemplate:
			self.executed = jsonTemplate['executed']

		if 'parameters' in jsonTemplate:
			# Hanlde old fils where parameters had only inputs
			if 'inputs' not in jsonTemplate['parameters'] and 'outputs' not in jsonTemplate['parameters']:
				jsonTemplate['parameters'] = dict(inputs=jsonTemplate['parameters'], outputs={})
			
			for io in ['inputs', 'outputs']:
				
				# Instead of overwriting parameters by doing self.parameters = jsonTemplate['parameters']
				# set the values one by one to avoid troubles with the out-of-date workflows which do not have all the parameters for the node
				for parameterName, serializedParameter in jsonTemplate['parameters'][io].items():
					parameters = self.parameters[io]
					if parameterName not in parameters:
						print(f'Warning: parameter "{parameterName}" does not exist in node "{self.name}". This means the saved file is out of date and does not correspond to the new inputs outputs definition.')
						continue
					parameter = parameters[parameterName]
					for key, value in serializedParameter.items():
						parameter[key] = value
					# 	if key == 'dataType' and value is not None:
					# 		parameter[key] = Path if serializedParameter.get('dataType') == 'Path' else locate(value)
					# 	else:
					# 		parameter[key] = value
					
					# # Convert serialized value to real type
					# if 'dataType' in parameter 	and parameter['value'] is not None:
					# 	parameter['value'] = parameter['dataType'](parameter['value'])

		if 'outputDataFramePath' in jsonTemplate and jsonTemplate['outputDataFramePath'] is not None:
			outputFolder = self.getOutputMetadataFolderPath()
			if Path(outputFolder / jsonTemplate['outputDataFramePath']).exists():
				self.setOutputAndClean(pandas.read_csv(outputFolder / jsonTemplate['outputDataFramePath'], index_col=0), False)
				if 'executed' in jsonTemplate:
					self.setExecuted(True)
			else:
				self.setExecuted(False, propagate=False, setDirty=True)

		# Connect inArray.dataBeenSet only if the graph is already built, otherwise it will be connected once the graph is built in Graph.populateFromJson()
		if not self.graph().populating:
			self.setupConnections()

	# update the parameters['inputs'] from data (but do not overwrite parameters['inputs'] which are already column names):
	# for all inputs which are auto, set the corresponding parameter to the column name
	def setParametersFromDataframe(self, data):
		n = len(data.columns)-1 if isinstance(data, pandas.DataFrame) else -1
		for input in self.tool.inputs:
			inputName = input['name']
			parameter = self.parameters['inputs'][inputName]
			if isinstance(data, pandas.DataFrame) and len(data)>0:
				paramIsAbsentColumn = parameter['type'] == 'columnName' and parameter['columnName'] not in data.columns
				paramIsUndefinedValue = parameter['type'] == 'value' and parameter.get('value', '') == ''
				if paramIsAbsentColumn or paramIsUndefinedValue:
					parameter['type'] = 'columnName'
					parameter['columnName'] = data.columns[max(0, n)]
					n -= 1
			elif parameter['type'] == 'columnName':
				parameter['type'] = 'value'

	# The input pin was plugged or parameters were changed in the properties GUI: set the node dirty & unexecuted
	def setNodeDirty(self, pin=None):
		self.setExecuted(executed=False, propagate=True, setDirty=True)
		self.compute()

	def getInputPins(self):
		return sorted( self.inArray.affected_by, key=lambda pin: pin.owningNode().y )
	
	def removeNones(self, items):
		return [i for i in items if i is not None]
	
	def getDataFrames(self):
		return self.removeNones([p.getCachedDataOrEvaluatdData() for p in self.getInputPins()])

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
		template = super().serialize()
		template['executed'] = self.executed
		template['parameters'] = self.parameters.copy()
		
		# template['folderDataFramePath'] = self.folderDataFramePath
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
	
	def getStem(self, filename):
		return Path(filename).stem
	
	def getSuffixes(self, filename):
		return filename[filename.index('.'):] if '.' in filename else ''

	# Check for {inputName}|.stem|.name.|.parent.name|.ext|.exts and replace by the real input value|file stem|file name|parent folder name|extension|extensions
	def replaceInputArgs(self, outputValue, inputGetter):
		for name in re.findall(r'\{([a-zA-Z0-9_-]+)\}', outputValue):
			input = inputGetter(name)
			if input is not None:
				outputValue = outputValue.replace(f'{{{name}}}', str(input))
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).stem\}', outputValue):
			input = inputGetter(name)
			if input is not None:
				outputValue = outputValue.replace(f'{{{name}.stem}}', self.getStem(input))
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).name\}', outputValue):
			input = inputGetter(name)
			if input is not None:
				outputValue = outputValue.replace(f'{{{name}.name}}', str(Path(input).name))
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).parent.name\}', outputValue):
			input = inputGetter(name)
			if input is not None:
				outputValue = outputValue.replace(f'{{{name}.parent.name}}', str(Path(input).parent.name))
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).ext\}', outputValue):
			input = inputGetter(name)
			if input is not None:
				outputValue = outputValue.replace(f'{{{name}.ext}}', Path(input).suffix)
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).exts\}', outputValue):
			input = inputGetter(name)
			if input is not None:
				outputValue = outputValue.replace(f'{{{name}.exts}}', ''.join(Path(input).suffixes))
		return outputValue

	def setOutputColumns(self, data):
		for outputName, output in self.parameters['outputs'].items():
			if output['dataType'] != 'Path': continue
			
			for index, row in data.iterrows():

				if output.get('value') is None:
					extension = output.get('extension', '') or ''
					finalValue = self.getWorkflowDataPath() / self.name / f'{outputName}_{index}{extension}'
				else:
					outputValue = str(output['value'])
					
					# Check that [workflow_folder] and [node_folder] are used at the beginning of the outputValue (if used at all)
					for name in ['[workflow_folder]', '[node_folder]']:
						if name in outputValue and not outputValue.startswith(name):
							raise Exception(f'Error: the special string "{name}" can only be used at the beginning of the output {outputName}.')
					
					# If outputValue is relative but does not contain [workflow_folder] nor [node_folder]: make it relative to the node_folder
					if ('[workflow_folder]' not in outputValue) and ('[node_folder]' not in outputValue) and (not Path(outputValue).is_absolute()):
						outputValue = '[node_folder]/' + outputValue
					
					# Check for {inputName}|.stem|.name.|.parent.name|.ext|.exts and replace by the real input value|file stem|file name|parent folder name|extension|extensions
					finalValue = self.replaceInputArgs(outputValue, (lambda name, row=row: self.getParameter(name, row)) )
					
					# Check for (columnName) and replace by the row value at this column
					for columnName in re.findall(r'\(([a-zA-Z0-9_-]+)\)', outputValue):
						if columnName in row:
							outputValue = outputValue.replace(f'({name})', str(row[columnName]))

					finalValue = finalValue.replace('[workflow_folder]', str(self.getWorkflowDataPath()))
					finalValue = finalValue.replace('[node_folder]', str(self.getWorkflowDataPath() / self.name))
					finalValue = finalValue.replace('[index]', str(index))
					if output.get('extension') is not None:
						finalValue = finalValue.replace('[ext]', output.get('extension'))

				data.at[index, self.getColumnName(outputName)] = finalValue # self.getWorkflowDataPath() / self.name / f'{finalStem}{indexString}{finalSuffix}'

	def mergeDataFrames(self, dataFrames):
		if len(dataFrames)==0: return pandas.DataFrame()
		result = pandas.concat(dataFrames, axis=1)
		# Remove duplicated columns
		result = result.loc[:,~result.columns.duplicated()].copy()
		# Replace every NaN with the first non-NaN value in the same column above it.
		# propagate[s] last valid observation forward to next valid
		result = result.ffill()
		return result

	def getDataFrame(self):
		if self.dataFrame is not None: return self.dataFrame
		dataFrames = self.getDataFrames()
		hasProcessDataFrames = hasattr(self.tool, 'processDataFrames') and callable(self.tool.processDataFrames)
		self.dataFrame = self.tool.processDataFrames(dataFrames, self.getArgs(False)) if hasProcessDataFrames else self.mergeDataFrames(dataFrames)
		self.setParametersFromDataframe(self.dataFrame)
		return self.dataFrame

	def compute(self, *args, **kwargs):
		if not self.dirty: return
		print('------------compute:', self.name)
		dataFrame = self.getDataFrame()
		self.setOutputColumns(dataFrame)
		if hasattr(self.tool, 'processDataFrame') and callable(self.tool.processDataFrame):
			dataFrame = self.tool.processDataFrame(dataFrame, self.getArgs(False))
		if hasattr(self.tool, 'outputMessage'):
			self.outputMessage = self.tool.outputMessage
		self.setOutputAndClean(dataFrame)
		ThumbnailGenerator.get().generateThumbnails(self.tool.name, dataFrame)
		return dataFrame

	def setOutputArgsFromDataFrame(self, args, outputData, index):
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
	
	def getWorkflowPath(self):
		graphManager = GraphManagerSingleton().get()
		return Path(graphManager.workflowPath).resolve()
	
	def getWorkflowDataPath(self):
		return self.getWorkflowPath() / 'Data'
	
	def getWorkflowToolsPath(self):
		return self.getWorkflowPath() / 'Tools'
	
	def setArg(self, args, parameterName, parameter, parameterValue, index):
		arg = parameterValue
		if parameter['dataType'] == 'Path' and arg is not None:
			arg = str(parameterValue)
			arg = arg.replace('[index]', str(index)) if index is not None else arg
			arg = arg.replace('[node_folder]', str(self.getWorkflowDataPath() / self.name))
			arg = arg.replace('[workflow_folder]', str(self.getWorkflowDataPath()))
			arg = Path(arg)
		args[parameterName] = arg
		return
	
	def parameterIsUndefinedAndRequired(self, parameterName, inputs, row=None):
		return any([toolInput.get('required') and self.getParameter(parameterName, row) is None for toolInput in inputs if toolInput['name'] == parameterName])
	
	def getArgs(self, raiseRequiredException=True):
		argsList = []
		inputData: pandas.DataFrame = self.inArray.currentData()
		outputData: pandas.DataFrame = self.outArray.currentData()
		if inputData is None:
			args = {}
			for parameterName, parameter in self.parameters['inputs'].items():
				if self.parameterIsUndefinedAndRequired(parameterName, self.tool.inputs) and raiseRequiredException:
					raise Exception(f'The parameter {parameterName} is undefined, but required.')
				self.setArg(args, parameterName, parameter, parameter['value'], None)
			self.setOutputArgsFromDataFrame(args, outputData, 0)
			argsList.append(args)
		else:
			for index, row in inputData.iterrows():
				args = {}
				for parameterName, parameter in self.parameters['inputs'].items():
					if self.parameterIsUndefinedAndRequired(parameterName, self.tool.inputs, row) and raiseRequiredException:
						raise Exception(f'The parameter {parameterName} is undefined, but required.')
					self.setArg(args, parameterName, parameter, self.getParameter(parameterName, row), index)
				self.setOutputArgsFromDataFrame(args, outputData, index)
				args['idf_row'] = row
				argsList.append(args)
		return [Munch.fromDict(args) for args in argsList]

	@classmethod
	def logLine(cls, line):
		inmain(lambda: cls.log.send(line.msg if isinstance(line, logging.LogRecord) else str(line)))
	
	@classmethod
	def logOutput(cls, process, stopEvent):
		try:
			for line in iter(process.stdout.readline, ''):  # Use iter to avoid buffering issues
				if stopEvent.is_set():
					break
				cls.logLine(line)
		except Exception as e:
			print(f"Exception in thread: {e}")
		return
	
	def execute(self):
		additionalInstallCommands = self.Tool.additionalInstallCommands if hasattr(self.Tool, 'additionalInstallCommands') else None
		additionalActivateCommands = self.Tool.additionalActivateCommands if hasattr(self.Tool, 'additionalActivateCommands') else None
		self.__class__.environment = environmentManager.createAndLaunch(self.Tool.environment, self.Tool.dependencies, additionalInstallCommands=additionalInstallCommands, additionalActivateCommands=additionalActivateCommands, mainEnvironment='bioimageit')
		if self.__class__.environment.process is not None:
			inthread(self.logOutput, self.__class__.environment.process, self.__class__.environment.stopEvent)
		argsList = self.getArgs()
		outputFolderPath = self.getOutputDataFolderPath()
		dataFrames = self.__class__.environment.execute('PyFlow.ToolManagement.ToolBase', 'processAllData', [self.Tool.moduleImportPath, argsList, outputFolderPath, self.getWorkflowToolsPath()]) or [None] * len(argsList)
		for i, args in enumerate(argsList):
			# The following log will also update the progress bar
			self.__class__.log.send(f'Process row [[{i+1}/{len(argsList)}]]')
			dataFrames[i] = self.__class__.environment.execute('PyFlow.ToolManagement.ToolBase', 'processData', [self.Tool.moduleImportPath, args, outputFolderPath, self.getWorkflowToolsPath()])
			if self.__class__.environment.stopEvent.is_set(): return False
		dataFrames = [df for df in dataFrames if df is not None]
		if len(dataFrames)>0:
			dataFrame = pandas.concat(dataFrames)
			self.setOutputAndClean(dataFrame)
		self.finishExecution(argsList)
		return True
	
	def saveArgsList(self, argsList, outputFolder):
		if argsList is None: return
		with open(outputFolder / PARAMETERS_PATH, 'w') as f:
			json.dump(argsList, f, default=lambda value: value.to_json(default_handler=str) if hasattr(value, 'to_json') and callable(value.to_json) else str(value))

	def finishExecution(self, argsList):
		outputFolder = self.getOutputMetadataFolderPath()
		outputFolder.mkdir(exist_ok=True, parents=True)

		outputData: pandas.DataFrame = self.outArray.currentData()
		ThumbnailGenerator.get().generateThumbnails(self.name, outputData)

		if isinstance(outputData, pandas.DataFrame):
			outputData.to_csv(outputFolder / OUTPUT_DATAFRAME_PATH)
		
		self.saveArgsList(argsList, outputFolder)
		self.setExecuted(True)

	def clear(self):
		self.deleteFiles()
		self.setExecuted(False, propagate=False, setDirty=False)
	
	def deleteFiles(self):
		ThumbnailGenerator.get().deleteThumbnails(self.name)
		for outputFolder in [self.getOutputDataFolderPath(), self.getOutputMetadataFolderPath()]:
			if outputFolder.exists():
				send2trash(outputFolder)

	def kill(self, *args, **kwargs):
		super().kill(*args, **kwargs)
		self.__class__.nodeDeteleted()
		
	@classmethod
	def nodeDeteleted(cls):
		cls.nInstanciatedNodes = max(cls.nInstanciatedNodes-1, 0)
		if cls.nInstanciatedNodes == 0:
			cls.exitTool()

	@classmethod
	def exitTool(cls):
		if cls.environment is not None:
			return environmentManager.exit(cls.environment)

	def getName(self):
		return self.name.replace('_', ' ').title()
	
	@classmethod
	def title(cls):
		return cls.Tool.title() if hasattr(cls.Tool, 'title') else super().title()

	@classmethod
	def description(cls): 
		return cls.Tool.description

	@classmethod
	def category(cls):
		return '|'.join(cls.Tool.categories)
	
def createNode(modulePath, moduleImportPath, module):
	# Hide the version number for now, but it would be nice to add it later when there are multiple versions of the tool
	# toolId = f'{tool.info.id}_v{tool.info.version}'
	if not hasattr(module, 'Tool'): return None
	module.Tool.moduleImportPath = moduleImportPath
	if not hasattr(module.Tool, 'environment'):
		module.Tool.environment = 'bioimageit'
	if not hasattr(module.Tool, 'dependencies'):
		module.Tool.dependencies = dict()
	for attr in ['name', 'description']:
		if not hasattr(module.Tool, attr):
			raise Exception(f'Tool {moduleImportPath} has no attribute {attr}.')
	# Creates a new class type named {modulePath.stem} which inherits BiitToolNode and have a Tool attribute
	toolClass = type(modulePath.stem, (BiitToolNode, ), dict(Tool=module.Tool))
	return toolClass

attachLogHandler(BiitToolNode.logLine)