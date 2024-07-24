import logging
import json
import sys
import re
from pathlib import Path
from munch import Munch
from PyFlow import getRootPath
from PyFlow.invoke_in_main import inthread, inmain
from PyFlow.Core.GraphManager import GraphManagerSingleton
from PyFlow.Packages.PyFlowBase.Tools.RunTool import RunTool
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase
from PyFlow.ToolManagement.EnvironmentManager import environmentManager, Environment, attachLogHandler

# class Status(Enum):
# 	STOPPED = 1
# 	LAUNCHING = 2
# 	LAUNCHED = 3


def get_bundle_path():
    return Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else getRootPath()

# path = Path(__file__).parent.resolve()
# with open(path.parent.parent / 'biit' / 'config.json' if path.name == 'ToolManagement' else path / 'biit' / 'config.json', 'r') as file:
# 	condaPath = Path(json.load(file)['runner']['conda_dir'])

environmentManager.setCondaPath(get_bundle_path() / 'micromamba')

class BiitToolNode(BiitArrayNodeBase):

	# status = Status.STOPPED
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
		super().kill(args, kwargs)
		self.__class__.nodeDeteleted()
	
	@property
	def packageName(self):
		return 'PyFlowBase'

	@classmethod
	def title(cls):
		return cls.Tool.title() if hasattr(cls.Tool, 'title') else super().title()
	
	@classmethod
	def nodeDeteleted(cls):
		cls.nInstanciatedNodes = max(cls.nInstanciatedNodes-1, 0)
		if cls.nInstanciatedNodes == 0:
			cls.exitTool()

	def actionToBiitType(self, action):
		if action.choices != None:
			return 'select'
		if action.const and type(action.default) is bool:
			return 'boolean'
		else:
			return {str: 'string', float: 'float', int: 'integer', Path: 'path', None: 'string'}[action.type]
		
	def initializeTool(self):
		tool = Munch.fromDict(dict(info=dict(id=self.name, inputs=[], outputs=[])))
		self.__class__.tool = tool
		# tool:
		#   info:
		#      categories:[]
		#      command: ''
		#      description: ''
		#      help: ''
		#      inputs:  default_value, description, help, is_advanced, is_data, name, type, value, select_info: names:[], values:[], value, type
		#      outputs:
		#      id: ''
		#      name: ''
		#      requiremenets: [{origin: '', type: '', env: '', init: '', package: ''}]
		#      tests: [[]]
		#    xml_file_url
		# toolInfo['inputs'].append({ key: value for key, value in input.__dict__.items() if key not in ['select_info']})
		for input in self.getToolIOs('inputs'):
			select_info = dict(names=input.choices, values=input.choices)
			tool.info.inputs.append(Munch.fromDict(dict(name=input.dest, type=self.actionToBiitType(input), is_advanced=False, value=input.default, help=input.help, description=input.help, default_value=input.default, select_info=select_info)))
		for output in self.getToolIOs('outputs'):
			select_info = dict(names=output.choices, values=output.choices)
			tool.info.outputs.append(Munch.fromDict(dict(name=output.dest, type=self.actionToBiitType(output), is_advanced=False, value=output.default, help=output.help, description=output.help, default_value=output.default, select_info=select_info)))
		return

	def getName(self):
		return self.name.replace('_', ' ').title()

	def getToolIOs(self, name):
		inputs_group = next( ac for ac in self.__class__.parser._action_groups if ac.title == name )
		return inputs_group._group_actions

	def postCreate(self, jsonTemplate=None):
		super().postCreate(jsonTemplate)
	
	def postCreateFinished(self):
		data = self.getDataFrame()
		self.parametersChanged.send(data)

	# @classmethod
	# def installTool(cls):
	# 	# Check environment exists
	# 	# If Tool has 'environment' and the environment does not exist: create it
	# 	if hasattr(cls.Tool, 'environment') and not (Path(ProcessBase.condaPath) / 'envs' / cls.Tool.environment).exists():
	# 		channel = f'{cls.Tool.environmentChannel}::' if hasattr(cls.Tool, 'channel') else ''
	# 		ProcessBase.executeCommands([ProcessBase.activateConda(), f'conda install {channel}{cls.Tool.environment}'])
	# 		return
	# 	# If Tool must be installed, meaning one of its dependency is not installed in the current environment: 
	# 	# create an environment and install dependencies
	# 	if cls.Tool.mustBeInstalled():
	# 		dependencies = " ".join(cls.Tool.dependencies)
	# 		ProcessBase.executeCommands([ProcessBase.activateConda(), f'conda create -n tool_{cls.toolName} {dependencies}'])

	# @classmethod
	# def launchToolIfNeeded(cls, callback=None):
	# 	if cls.status == Status.STOPPED:
	# 		cls.status = Status.LAUNCHING
	# 		cls.worker = Worker(lambda progress_callback: cls.launchTool(force=True))
	# 		if callback is not None:
	# 			cls.worker.signals.finished.connect(callback)
	# 		ProcessBase.setClassPort() # Set class port (check ports until one is available) in synchronous manner, before launching the thread, otherwise every tool gets the same port
	# 		QThreadPool.globalInstance().start(cls.worker)
	# 	elif cls.status == Status.LAUNCHING:
	# 		if callback is not None:
	# 			cls.worker.signals.finished.connect(callback)
	# 	else:
	# 		callback()
	
	# @classmethod
	# def launchTool(cls, force=False, blocking=False):
	# 	if not cls.Tool.mustBeInstalled():
	# 		cls.status = Status.LAUNCHED
	# 		return
	# 	if cls.status == Status.STOPPED or force:
	# 		cls.installTool()
	# 		cls.port = ProcessBase.port
	# 		ProcessBase.executeCommands([ProcessBase.activateConda(), f'conda activate {cls.Tool.environment}', 'cd PyFlow/Tools/', f'python "{cls.toolPath.resolve()}" --listener_port {cls.port}'], f'Listen {ProcessBase.host}:{cls.port}')
	# 		cls.connection = Client((ProcessBase.host, cls.port))
	# 		cls.status = Status.LAUNCHED
	# 	if blocking:
	# 		cls.waitForProcessToBeLaunched()

	# @classmethod
	# def waitForProcessToBeLaunched(cls):
	# 	if cls.status == Status.LAUNCHED: return
	# 	if cls.status != Status.LAUNCHING: raise('Error: the process is stopped, not launching (nor launched).')
	# 	timer = QTimer()
	# 	timer.setSingleShot(True)
	# 	loop = QEventLoop()
	# 	cls.worker.signals.finished.connect(loop.quit)
	# 	timer.timeout.connect(loop.quit)
	# 	timer.start(5000)
	# 	loop.exec()

	@classmethod
	def exitTool(cls):
		# if not cls.Tool.mustBeInstalled():
		# 	cls.status = Status.STOPPED
		# 	return
		# if cls.status == Status.LAUNCHING:
		# 	# It would be better to be able to kill the worker
		# 	cls.waitForProcessToBeLaunched()
		# if cls.status == Status.LAUNCHED:
		# 	cls.connection.send(dict(action='exit'))
		# 	cls.connection.close()
		# cls.status = Status.STOPPED
		if cls.environment is not None:
			return environmentManager.exit(cls.environment)

	def getParameterValueString(self, name, row):
		parameterDict = self.parameters[name]
		if parameterDict['type'] == 'value':
			return str(parameterDict['value'])
		else:
			value = row[parameterDict['columnName']]
			return value.stem if isinstance(value, Path) else value
	
	def replaceInputArgs(self, outputValue, inputGetter):
		for name in re.findall(r'\{([a-zA-Z0-9_-]+)\}', str(outputValue)):
			outputValue = str(outputValue).replace(f'{{{name}}}', str(inputGetter(name)))
		return outputValue

	def setOutputColumns(self, tool, data):
		graphManager = GraphManagerSingleton().get()
		for output in tool.info.outputs:
			if output.type != 'path': continue
			ods = output.default_value.split('.')
			stem = ods[0]
			suffixes = '.'.join(ods[1:])
			# data[self.getColumnName(output)] = [Path(graphManager.workflowPath).resolve() / self.name / f'{stem}_{i}.{suffixes}' for i in range(len(data))]
			for index, row in data.iterrows():
				finalStem = self.replaceInputArgs(stem, lambda name: self.getParameterValueString(name, row))
				data.at[index, self.getColumnName(output)] = Path(graphManager.workflowPath).resolve() / self.name / f'{finalStem}_{index}.{suffixes}'

	def compute(self):
		data = super().compute()
		if data is None: return
		return self.tool.processDataFrame(data)
	
	@classmethod
	def logLine(cls, line):
		inmain(lambda: cls.log.send(line.msg if isinstance(line, logging.LogRecord) else str(line)))

	@classmethod
	def logOutput(cls, process):
		for line in process.stdout:
			cls.logLine(line)
		return
	
	def execute(self, req):
		self.__class__.environment = environmentManager.createAndLaunch(self.Tool.environment, self.Tool.dependencies)
		inthread(self.logOutput, self.__class__.environment.process)
		# self.worker = Worker(lambda progress_callback: self.logOutput(self.__class__.environment.process, logTool))
		# QThreadPool.globalInstance().start(self.worker)
		argsList = self.getArgs()
		for i, args in enumerate(argsList):
			# The following log will also update the progress bar
			self.__class__.log.send(f'Process row [[{i+1}/{len(argsList)}]]')
			args = [item for items in [(f'--{key}', f'{value}') for key, value in args.items()] for item in items]
			self.__class__.environment.execute('PyFlow.ToolManagement.ToolBase', 'processData', [self.toolImportPath, args])
		self.setExecuted(True)
		return

def constructor(self, name):
	super(self.__class__, self).__init__(name)

def compute(self, *args, **kwargs):
	return super(self.__class__, self).compute(**kwargs)
	
@classmethod
def description(cls): 
	return cls.parser.description

@classmethod
def category(cls):
	return '|'.join(cls.Tool.categories)

def createNode(modulePath, moduleImportPath, module):
	# Hide the version number for now, but it would be nice to add it later when there are multiple versions of the tool
	# toolId = f'{tool.info.id}_v{tool.info.version}'
	# toolId = f'{tool.info.id}_biitarray'

	parser = module.Tool.getArgumentParser()

	# Creates a new class type named {modulePath.stem} which inherits BiitToolNode and have the attributes of the given dict
	toolClass = type(modulePath.stem, (BiitToolNode, ), dict( 
		parser = parser,
		toolName = modulePath.stem,
		toolPath = modulePath,
		toolImportPath = moduleImportPath,
		Tool = module.Tool,
		__init__= constructor, 
		compute = compute, 
		description = description,
		category = category
	))
	return toolClass

attachLogHandler(BiitToolNode.logLine)