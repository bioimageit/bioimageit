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
	def nodeDeteleted(cls):
		cls.nInstanciatedNodes = max(cls.nInstanciatedNodes-1, 0)
		if cls.nInstanciatedNodes == 0:
			cls.exitTool()

	def postCreateFinished(self):
		data = self.getDataFrame()
		self.parametersChanged.send(data)

	@classmethod
	def exitTool(cls):
		if cls.environment is not None:
			return environmentManager.exit(cls.environment)

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

def createNode(modulePath, moduleImportPath, module):
	# Hide the version number for now, but it would be nice to add it later when there are multiple versions of the tool
	# toolId = f'{tool.info.id}_v{tool.info.version}'
	if not hasattr(module, 'Tool'): return None
	module.Tool.moduleImportPath = moduleImportPath
	# Creates a new class type named {modulePath.stem} which inherits BiitToolNode and have the attributes of the given dict
	toolClass = type(modulePath.stem, (BiitToolNode, ), vars(module.Tool))
	return toolClass

attachLogHandler(BiitToolNode.logLine)