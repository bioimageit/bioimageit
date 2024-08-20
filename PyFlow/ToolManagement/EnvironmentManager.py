import logging
import platform
import tempfile
import subprocess
from importlib import metadata
from importlib import import_module
from pathlib import Path
from collections.abc import Callable
from abc import abstractmethod
from multiprocessing.connection import Client
import sys
if sys.version_info < (3, 11):
    from typing_extensions import TypedDict, Required, NotRequired, Self
else:
    from typing import TypedDict, Required, NotRequired, Self

# class Singleton(type):
# 	_instances = {}
# 	def __call__(cls, *args, **kwargs):
# 		if cls not in cls._instances:
# 			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
# 		return cls._instances[cls]

logger = logging.getLogger(__name__)

class CustomHandler(logging.Handler):

	def __init__(self, log)-> None:
		logging.Handler.__init__(self=self)
		self.log = log

	def emit(self, record: logging.LogRecord) -> None:
		self.log(record)

def attachLogHandler(log:Callable[[str], None], logLevel=logging.INFO) -> None:
	logger.setLevel(logLevel)
	ch = CustomHandler(log)
	ch.setLevel(logLevel)
	logger.addHandler(ch)
	return

class Dependencies(TypedDict):
	python: str
	conda: NotRequired[list[str]]
	pip: NotRequired[list[str]]

class Environment():
	
	def __init__(self, name) -> None:
		self.name = name
		self.process = None

	@abstractmethod
	def execute(self, module:str, function: str, args: list):
		return
	
	@abstractmethod
	def _exit(self):
		return

	def launched(self):
		return True
		
class ClientEnvironment(Environment):
	def __init__(self, name, port, process: subprocess.Popen) -> None:
		super().__init__(name)
		self.port = port
		self.process = process
		self.connection = None
		# self.nTries = 0
	
	def initialize(self):
		self.connection = Client((EnvironmentManager.host, self.port))
	
	def execute(self, module:str, function: str, args: list):
		self.connection.send(dict(action='execute', module=module, function=function, args=args))
		while message := self.connection.recv():
			if message['action'] == 'execution finished':
				logger.info('execution finished')
				return message['result'] if 'result' in message else None
			elif message['action'] == 'error':
				raise Exception(message)
			# if message['action'] == 'print':
			# 	print(message['content'])
			else:
				logger.warning('Got an unexpected message: ', message)
		# try:
		# except EOFError as e:
		# 	if self.nTries > 1:
		# 		raise e
		# 	self.initialize()
		# 	self.execute(module, function, args)
		# 	self.nTries += 1
	
	def launched(self):
		return self.connection is not None and self.connection.writable and self.connection.readable and not self.connection.closed
	
	def _exit(self):
		if self.connection is not None:
			try:
				self.connection.send(dict(action='exit'))
			except OSError as e:
				if e.args[0] == 'handle is closed': pass
			self.connection.close()
		self.process.kill()
		return
	
	# def __enter__(self):
	# 	return self.initialize()
	
	# def __exit__(self, exc_type, exc_value, traceback):
	# 	return self.exit()
	
	# def __del__(self):
	# 	self.exit()
	
class DirectEnvironment(Environment):
	def __init__(self, name) -> None:
		super().__init__(name)
		self.modules = {}

	def execute(self, module:str, function: str, args: list):
		if module not in self.modules:
			self.modules[module] = import_module(module)
		if not hasattr(self.modules[module], function):
			raise Exception(f'Module {module} has no function {function}.')
		return getattr(self.modules[module], function)(*args)

	def _exit(self):
		return

# class EnvironmentManager(metaclass=Singleton):
class EnvironmentManager:

	condaBin = 'micromamba'
	host = 'localhost'
	environments: dict[str, Environment] = {}
	
	def __init__(self, condaPath:str|Path=Path('micromamba')) -> None:
		self.setCondaPath(condaPath)
	
	def setCondaPath(self, condaPath:str|Path):
		self.condaPath = Path(condaPath)
	
	def _insertCommandErrorChecks(self, commands):
		commandsWithChecks = []
		errorMessage = 'Errors encountered during execution. Exited with status:'
		# windowsChecks = ['', 'if errorlevel 1 exit 1']
		# windowsChecks = ['', 'if %ERRORLEVEL% == 0 goto :next', 
		# 	f'echo "{errorMessage} %errorlevel%"', 
		# 	'goto :endofscript\n', '']
		windowsChecks = ['', 'if (! $?) { exit 1 } ']
		posixChecks = ['', 'return_status=$?', 
			'if [ $return_status -ne 0 ]', 
			'then', 
			f'    echo "{errorMessage} $return_status"', 
			'    exit 1', 
			'fi', '']
		checks = windowsChecks if self._isWindows() else posixChecks
		for command in commands:
			commandsWithChecks.append(command)
			commandsWithChecks += checks
		return commandsWithChecks

	def _getOutput(self, process:subprocess.Popen, commands:list[str]=None):
		commands = str(commands) if commands is not None and len(commands)>0 else ''
		outputs = []
		for line in process.stdout:
			logger.info(line)
			if 'CondaSystemExit' in line:
				process.kill()
				raise Exception(f'An error occured during the execution of the commands {commands}.')
			outputs.append(line)
		process.wait()
		if process.returncode != 0:
			raise Exception(f'An error occured during the execution of the commands {commands}.')
		return (outputs, process.returncode)

	# If launchMessage is defined: execute until launchMessage is print
	# else: execute completely (blocking)
	def executeCommands(self, commands: list[str], launchedMessage:str=None, env:dict[str, str]=None, exitIfCommandError=True):
		print('executeCommands', commands, launchedMessage)

		with tempfile.NamedTemporaryFile(suffix='.ps1' if self._isWindows() else '.sh', mode='w', delete=False) as tmp:
			if exitIfCommandError:
				commands = self._insertCommandErrorChecks(commands)
			tmp.write('\n'.join(commands))
			tmp.flush()
			executeFile = ['powershell', '-NoProfile', '-ExecutionPolicy', 'ByPass', '-File', tmp.name] if self._isWindows() else ['/bin/bash', tmp.name]
			if not self._isWindows():
				subprocess.run(['chmod', 'u+x', tmp.name])
			print(tmp.name)
			# Use UTF-8 encoding since it's the default on Linux, Mac, and Powershell on Windows
			return subprocess.Popen(executeFile, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, encoding='utf-8', bufsize=1)

	def _removeChannel(self, condaDependency):
		return condaDependency.split('::')[1]
	
	def environmentIsRequired(self, dependencies: Dependencies):
		if 'conda' in dependencies and len(dependencies['conda'])>0:
			process = self.executeCommands([self._activateConda(), f'{self.condaBin} list -y'])
			out, _ = self._getOutput(process)
			installedCondaPackages = out.split('\n')
			if not all([self._removeChannel(d) in installedCondaPackages for d in dependencies['conda']]):
				return True
		if 'pip' not in dependencies: return False
		dists = [f'{dist.metadata["Name"]}=={dist.version}' for dist in metadata.distributions()]
		return not all([d in dists for d in dependencies['pip']])

	def _isWindows(self):
		return platform.system() == 'Windows'
	
	def _getCondaPaths(self):
		return self.condaPath.resolve(), Path('bin/micromamba' if platform.system() != 'Windows' else 'Library/bin/micromamba.exe')

	def _setupCondaChannels(self):
		return [f'{self.condaBin} config append channels conda-forge', f'{self.condaBin} config append channels nodefaults', f'{self.condaBin} config set channel_priority flexible']
	
	def _shellHook(self):
		currentPath = Path.cwd().resolve()
		condaPath, condaBinPath = self._getCondaPaths()
		if platform.system() == 'Windows':
			return [f'Set-Location -Path "{condaPath}"', f'$Env:MAMBA_ROOT_PREFIX="{condaPath}"', f'{condaBinPath} shell hook -s powershell | Out-String | Invoke-Expression', f'Set-Location -Path "{currentPath}"']
		else:
			return [f'cd "{condaPath}"', f'export MAMBA_ROOT_PREFIX="{condaPath}"', f'eval "$({condaBinPath} shell hook -s posix)"', f'cd "{currentPath}"']
	
	def _installCondaIfNecessary(self):
		condaPath, condaBinPath = self._getCondaPaths()
		if (condaPath / condaBinPath).exists(): return []
		if platform.system() not in ['Windows', 'Linux', 'Darwin']:
			raise Exception(f'Platform {platform.system()} is not supported.')
		condaPath.mkdir(exist_ok=True, parents=True)
		commands = []
		if platform.system() == 'Windows':
			commands += [f'Set-Location -Path "{condaPath}"', 
		   			'Invoke-Webrequest -URI https://micro.mamba.pm/api/micromamba/win-64/latest -OutFile micromamba.tar.bz2', 
					'if (Test-Path micromamba.tar) {',
						'Remove-Item micromamba.tar -verbose',
					'}',
					'bzip2 -d micromamba.tar.bz2',
		   			'tar xf micromamba.tar',
					'Remove-Item micromamba.tar']
		else:
			system = 'osx' if platform.system() == 'Darwin' else 'linux'
			machine = platform.machine()
			machine = '64' if machine == 'x86_64' else machine
			commands += [f'cd "{condaPath}"', f'curl -Ls https://micro.mamba.pm/api/micromamba/{system}-{machine}/latest | tar -xvj bin/micromamba']
		commands += self._shellHook()
		return commands + self._setupCondaChannels()

	def _activateConda(self):
		# activatePath = Path(self.condaPath) / 'condabin' / 'conda.bat' if self._isWindows() else Path(self.condaPath) / 'etc' / 'profile.d' / 'conda.sh'
		# return f'"{activatePath}" ' if self._isWindows() else f'. "{activatePath}"'
		commands = self._installCondaIfNecessary()
		return commands + self._shellHook()

	def environmentExists(self, environment:str):
		condaMeta = Path(self.condaPath) / 'envs' / environment / 'conda-meta'
		return condaMeta.is_dir() # we could also check for the condaMeta / history file.
	
	def install(self, environment:str, channel=None):
		channel = channel + '::' if channel is not None else ''
		process = self.executeCommands(self._activateConda() + [f'{self.condaBin} install {channel}{environment} -y'])
		self._getOutput(process)

	def formatDependencies(self, package_manager:str, dependencies: list[str]):
		dependencies = dependencies[package_manager] if package_manager in dependencies else []
		return [f'"{d}"' for d in dependencies]
	
	def create(self, environment:str, dependencies:Dependencies={}, skipIfDependenciesAreAvailable=False, errorIfExists=False) -> bool:
		if skipIfDependenciesAreAvailable and not self.environmentIsRequired(dependencies): return False
		if self.environmentExists(environment):
			if errorIfExists:
				raise Exception(f'Error: the environment {environment} already exists.')
			else:
				return True
		pythonRequirement = dependencies['python'] if 'python' in dependencies and dependencies['python'] else ''
		condaDependencies = self.formatDependencies('conda', dependencies)
		pipDependencies = self.formatDependencies('pip', dependencies)
		createEnvCommands = self._activateConda() + [f'{self.condaBin} create -n {environment} python{pythonRequirement} -y']
		createEnvCommands += [f'{self.condaBin} activate {environment}'] if len(condaDependencies) > 0 or len(pipDependencies) > 0 else []
		createEnvCommands += [f'{self.condaBin} install {" ".join(condaDependencies)} -y'] if len(condaDependencies)>0 else []
		createEnvCommands += [f'pip install {" ".join(pipDependencies)}'] if len(pipDependencies)>0 else []
		process = self.executeCommands(createEnvCommands)
		self._getOutput(process)
		return True
	
	def _environmentIsLaunched(self, environment:str):
		return environment in self.environments and self.environments[environment].launched()
	
	# Unusued, but could be nice
	# def executeCommandsInEnvironment(self, environment:str, commands:list[str], environmentVariables:dict[str, str]=None):
	# 	commands = self._activateConda() + [f'{self.condaBin} activate {environment}'] + commands
	# 	return self.executeCommands(commands, env=environmentVariables)

	def launch(self, environment:str, customCommand:str=None, environmentVariables:dict[str, str]=None, condaEnvironment=True) -> Environment:
		if self._environmentIsLaunched(environment):
			return self.environments[environment]

		moduleCallerPath = Path(__file__).parent / 'ModuleCaller.py'
		commands = self._activateConda() + [f'{self.condaBin} activate {environment}'] if condaEnvironment else []
		commands += [f'python -u "{moduleCallerPath}"' if customCommand is None else customCommand]
		process = self.executeCommands(commands, env=environmentVariables)
		# The python command is called with the -u (unbuffered) option, we can wait for a specific print before letting the process run by itself
		# if the unbuffered option is not set, the following can wait for the whole python process to finish
		port = -1
		for line in process.stdout:
			logger.info(line)
			if line.strip().startswith('Listening port '):
				port = int(line.strip().replace('Listening port ', ''))
				break
		# If process is finished: check if error
		if process.poll() is not None:
			raise Exception(f'Process exited with return code {process.returncode}.')
		ce = ClientEnvironment(environment, port, process)
		self.environments[environment] = ce
		ce.initialize()
		return ce
	
	# @contextmanager
	def createAndLaunch(self, environment:str, dependencies:Dependencies={}, customCommand:str=None, environmentVariables:dict[str, str]=None) -> Environment:
		environmentIsRequired = self.create(environment, dependencies, True)
		if environmentIsRequired:
			return self.launch(environment, customCommand, environmentVariables)
			# ce = self.launch(environment)
			# try:
			# 	yield ce
			# finally:
			# 	ce.exit()
		else:
			return DirectEnvironment(environment)
	
	def exit(self, environment:Environment|str):
		environmentName = environment if isinstance(environment, str) else environment.name
		if environmentName in self.environments:
			self.environments[environmentName]._exit()
			del self.environments[environmentName]
	
environmentManager = EnvironmentManager()