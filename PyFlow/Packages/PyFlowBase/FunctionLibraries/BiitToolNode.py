import logging
import subprocess
import re
import pandas
from pathlib import Path
from munch import Munch
from PyFlow import getBundlePath
from PyFlow.invoke_in_main import inthread, inmain
from PyFlow.Core.GraphManager import GraphManagerSingleton
from PyFlow.Packages.PyFlowBase.Tools.RunTool import RunTool
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitArrayNode import BiitArrayNodeBase
from PyFlow.ToolManagement.EnvironmentManager import environmentManager, Environment, attachLogHandler

# class Status(Enum):
# 	STOPPED = 1
# 	LAUNCHING = 2
# 	LAUNCHED = 3

# path = Path(__file__).parent.resolve()
# with open(path.parent.parent / 'biit' / 'config.json' if path.name == 'ToolManagement' else path / 'biit' / 'config.json', 'r') as file:
# 	condaPath = Path(json.load(file)['runner']['conda_dir'])

environmentManager.setCondaPath(getBundlePath() / 'micromamba')

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
		for input in self.getInputArgs():
			select_info = dict(names=input.choices, values=input.choices)
			auto = self.__class__.argsOptions[input.dest]['autoColumn'] if input.dest in self.__class__.argsOptions and 'autoColumn' in self.__class__.argsOptions[input.dest] else False
			tool.info.inputs.append(Munch.fromDict(dict(name=input.dest, type=self.actionToBiitType(input), is_advanced=input.container.title == 'advanced', value=input.default, help=input.help, description=input.help, default_value=input.default, select_info=select_info, auto=auto)))
		for output in self.getOutputArgs():
			select_info = dict(names=output.choices, values=output.choices)
			auto_increment = self.__class__.argsOptions[output.dest]['autoIncrement'] if output.dest in self.__class__.argsOptions and 'autoIncrement' in self.__class__.argsOptions[output.dest] else True
			tool.info.outputs.append(Munch.fromDict(dict(name=output.dest, type=self.actionToBiitType(output), is_advanced=False, value=output.default, help=output.help, description=output.help, default_value=output.default, select_info=select_info, auto_increment=auto_increment)))
		return

	def getName(self):
		return self.name.replace('_', ' ').title()

	def getArgGroup(self, name):
		argGroup = [ag for ag in self.__class__.parser._action_groups if ag.title == name]
		return argGroup[0] if len(argGroup) > 0 else None

	def getInputArgs(self):
		inputs = self.getArgGroup('inputs')
		if inputs is None: return []
		return inputs._group_actions + [ac for ag in inputs._action_groups for ac in ag._group_actions]

	def getOutputArgs(self):
		outputs = self.getArgGroup('outputs')
		return outputs._group_actions if outputs is not None else []

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

	def getStem(self, filename):
		filename = filename[:-1] if filename.endswith('/') else filename
		return filename[:filename.index('.')] if '.' in filename else filename
	
	def getSuffixes(self, filename):
		return filename[filename.index('.'):] if '.' in filename else ''

	def replaceInputArgs(self, outputValue, inputGetter):
		for name in re.findall(r'\{([a-zA-Z0-9_-]+)\}', str(outputValue)):
			input = inputGetter(name)
			if input is not None:
				outputValue = str(outputValue).replace(f'{{{name}}}', input)
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).stem\}', str(outputValue)):
			input = inputGetter(name)
			if input is not None:
				outputValue = str(outputValue).replace(f'{{{name}.stem}}', self.getStem(str(input)))
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).name\}', str(outputValue)):
			input = inputGetter(name)
			if input is not None:
				outputValue = str(outputValue).replace(f'{{{name}.name}}', str(Path(input).name))
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).parent.name\}', str(outputValue)):
			input = inputGetter(name)
			if input is not None:
				outputValue = str(outputValue).replace(f'{{{name}.parent.name}}', str(Path(input).parent.name))
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).ext\}', str(outputValue)):
			input = inputGetter(name)
			if input is not None:
				outputValue = str(outputValue).replace(f'{{{name}.ext}}', Path(input).suffix)
		for name in re.findall(r'\{([a-zA-Z0-9_-]+).exts\}', str(outputValue)):
			input = inputGetter(name)
			if input is not None:
				outputValue = str(outputValue).replace(f'{{{name}.exts}}', ''.join(Path(input).suffixes))
		return outputValue

	def getParameterValueName(self, name, row):
		parameterValue = self.getParameter(name, row)
		return parameterValue.name if isinstance(parameterValue, Path) else str(parameterValue)

	def setBoolArg(self, args, name):
		args[name] = True

	def setOutputColumns(self, tool, data):
		graphManager = GraphManagerSingleton().get()
		for output in tool.info.outputs:
			if output.type != 'path': continue
			# ods = output.default_value.split('.')
			# stem = ods[0]
			# suffixes = '.'.join(ods[1:])
			# data[self.getColumnName(output)] = [Path(graphManager.workflowPath).resolve() / self.name / f'{stem}_{i}.{suffixes}' for i in range(len(data))]
			for index, row in data.iterrows():
				# finalValue = self.replaceInputArgs(output.default_value, lambda name: self.getParameterValueName(name, row))
				finalValue = self.replaceInputArgs(output.default_value, lambda name: self.getParameter(name, row))
				finalStem, finalSuffix = self.getStem(finalValue), self.getSuffixes(finalValue)
				indexString = f'_{index}' if len(data)>1 and output.auto_increment else ''
				data.at[index, self.getColumnName(output)] = Path(graphManager.workflowPath).resolve() / self.name / f'{finalStem}{indexString}{finalSuffix}'

	def compute(self):
		data = super().compute()
		if data is None: return
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
	def logOutput(cls, process):
		for line in process.stdout:
			cls.logLine(line)
		return
	
	def execute(self, req):
		self.__class__.environment = environmentManager.createAndLaunch(self.Tool.environment, self.Tool.dependencies)
		if self.__class__.environment.process is not None:
			inthread(self.logOutput, self.__class__.environment.process)
		# self.worker = Worker(lambda progress_callback: self.logOutput(self.__class__.environment.process, logTool))
		# QThreadPool.globalInstance().start(self.worker)
		argsList = self.getArgs()
		# for i, args in enumerate(argsList):
		# 	argsList[i] = [item for items in [(f'--{key}',) if isinstance(value, bool) and value else (f'--{key}', f'{value}') for key, value in args.items()] for item in items]
		
		self.__class__.environment.execute('PyFlow.ToolManagement.ToolBase', 'processAllData', [self.toolImportPath, argsList])
		for i, args in enumerate(argsList):
			# The following log will also update the progress bar
			self.__class__.log.send(f'Process row [[{i+1}/{len(argsList)}]]')
			args = [item for items in [(f'--{key}',) if isinstance(value, bool) and value else (f'--{key}', f'{value}') for key, value in args.items()] for item in items]
			completedProcess: subprocess.CompletedProcess = self.__class__.environment.execute('PyFlow.ToolManagement.ToolBase', 'processData', [self.toolImportPath, args])
			if completedProcess is not None and completedProcess.returncode != 0:
				raise Exception(completedProcess)
		self.finishExecution(argsList)
		return True

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

	parser, argsOptions = module.Tool.getArgumentParser()

	# Creates a new class type named {modulePath.stem} which inherits BiitToolNode and have the attributes of the given dict
	toolClass = type(modulePath.stem, (BiitToolNode, ), dict( 
		parser = parser,
		argsOptions = argsOptions,
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