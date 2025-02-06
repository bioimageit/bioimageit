import logging
import subprocess
import re
import pandas
from pathlib import Path
from munch import Munch
from PyFlow import getRootPath
from PyFlow.invoke_in_main import inthread, inmain
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase
from PyFlow.ToolManagement.EnvironmentManager import environmentManager, Environment, attachLogHandler

environmentManager.setCondaPath(getRootPath() / 'micromamba')

class BiitToolNode(BiitArrayNodeBase):

	nInstanciatedNodes = 0
	MAX_CONNECTION_TRIES = 100
	environment: Environment = None

	def __init__(self, name):
		super().__init__(name)
		self.initializeTool()
		self.tool = None
		self.tool = self.Tool()
		self.__class__.nInstanciatedNodes += 1
	
	def kill(self, *args, **kwargs):
		super().kill(*args, **kwargs)
		self.__class__.nodeDeteleted()
	
	@classmethod
	def title(cls):
		return cls.Tool.title() if hasattr(cls.Tool, 'title') else super().title()
	
	@classmethod
	def nodeDeteleted(cls):
		cls.nInstanciatedNodes = max(cls.nInstanciatedNodes-1, 0)
		if cls.nInstanciatedNodes == 0:
			cls.exitTool()

	def getName(self):
		return self.name.replace('_', ' ').title()

	def postCreateFinished(self):
		data = self.getDataFrame()
		self.parametersChanged.send(data)

	@classmethod
	def exitTool(cls):
		if cls.environment is not None:
			return environmentManager.exit(cls.environment)

	def getStem(self, filename):
		return Path(filename).stem
	
	def getSuffixes(self, filename):
		return filename[filename.index('.'):] if '.' in filename else ''

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

	def getParameterValueName(self, name, row):
		parameterValue = self.getParameter(name, row)
		return parameterValue.name if isinstance(parameterValue, Path) else str(parameterValue)

	def setBoolArg(self, args, name):
		args[name] = True

	def setOutputColumns(self, tool, data):
		for outputName, output in self.parameters['outputs'].items():
			if output['type'] != 'path': continue
			
			for index, row in data.iterrows():

				if 'value' not in output or output['value'] is None:
					extension = output['extension'] if 'extension' in extension else ''
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
					
					finalValue = self.replaceInputArgs(outputValue, (lambda name, row=row: self.getParameter(name, row)) )
					# finalStem, finalSuffix = self.getStem(finalValue), self.getSuffixes(finalValue)
					
					finalValue = finalValue.replace('[workflow_folder]', str(self.getWorkflowDataPath()))
					finalValue = finalValue.replace('[node_folder]', str(self.getWorkflowDataPath() / self.name))
					finalValue = finalValue.replace('[index]', str(index))

				data.at[index, self.getColumnName(outputName)] = finalValue # self.getWorkflowDataPath() / self.name / f'{finalStem}{indexString}{finalSuffix}'

	def compute(self):
		data = self.updateDataFrameIfDirty()
		if data is None: return
		if hasattr(self.tool, 'processDataFrame') and callable(self.tool.processDataFrame):
			data = self.tool.processDataFrame(data, [Munch.fromDict(args) for args in self.getArgs()])
		self.setOutputAndClean(data if isinstance(data, pandas.DataFrame) else data['dataFrame'])
		if (not isinstance(data, pandas.DataFrame)) and 'outputMessage' in data:
			self.outputMessage = data['outputMessage']
			return data['dataFrame']
		return data
	
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
	
	def execute(self, req):
		additionalInstallCommands = self.Tool.additionalInstallCommands if hasattr(self.Tool, 'additionalInstallCommands') else None
		additionalActivateCommands = self.Tool.additionalActivateCommands if hasattr(self.Tool, 'additionalActivateCommands') else None
		self.__class__.environment = environmentManager.createAndLaunch(self.Tool.environment, self.Tool.dependencies, additionalInstallCommands=additionalInstallCommands, additionalActivateCommands=additionalActivateCommands, mainEnvironment='bioimageit')
		if self.__class__.environment.process is not None:
			inthread(self.logOutput, self.__class__.environment.process, self.__class__.environment.stopEvent)
		# self.worker = Worker(lambda progress_callback: self.logOutput(self.__class__.environment.process, logTool))
		# QThreadPool.globalInstance().start(self.worker)
		argsList = self.getArgs()
		for i, args in enumerate(argsList):
			argsList[i] = [item for items in [(f'--{key}',) if isinstance(value, bool) and value else (f'--{key}', f'{value}') for key, value in args.items()] for item in items]
		outputFolderPath = self.getOutputDataFolderPath()
		completedProcess: subprocess.CompletedProcess = self.__class__.environment.execute('PyFlow.ToolManagement.ToolBase', 'processAllData', [self.toolImportPath, argsList, outputFolderPath, self.getWorkflowToolsPath()])
		if completedProcess is None and self.__class__.environment.stopEvent.is_set(): return False
		if completedProcess is not None and completedProcess.returncode != 0:
			raise Exception(completedProcess)
		for i, args in enumerate(argsList):
			# The following log will also update the progress bar
			self.__class__.log.send(f'Process row [[{i+1}/{len(argsList)}]]')
			# args = [item for items in [(f'--{key}',) if isinstance(value, bool) and value else (f'--{key}', f'{value}') for key, value in args.items()] for item in items]
			completedProcess: subprocess.CompletedProcess = self.__class__.environment.execute('PyFlow.ToolManagement.ToolBase', 'processData', [self.toolImportPath, args, outputFolderPath, self.getWorkflowToolsPath()])
			if completedProcess is None and self.__class__.environment.stopEvent.is_set(): return False
			if completedProcess is not None and completedProcess.returncode != 0:
				raise Exception(completedProcess)
		self.finishExecution(argsList)
		return True

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
	# Creates a new class type named {modulePath.stem} which inherits BiitToolNode and have the attributes of the given dict
	toolClass = type(modulePath.stem, (BiitToolNode, ), vars(module.Tool))
	return toolClass

attachLogHandler(BiitToolNode.logLine)