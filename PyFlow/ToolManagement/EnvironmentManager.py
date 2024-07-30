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
from typing import TypedDict

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
	python: float
	conda: list[str]
	pip: list[str]

class Environment():
	
	def __init__(self, name) -> None:
		self.name = name

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
				break
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
	
class ProxyEnvironment(Environment):
	def __init__(self, name) -> None:
		super().__init__(name)
		self.modules = {}

	def execute(self, module:str, function: str, args: list):
		if module not in self.modules:
			self.modules[module] = import_module(module)
			if not hasattr(module, function):
				raise Exception(f'Module {module} has no function {function}.')
			getattr(module, function)(**args)

	def _exit(self):
		return

# class EnvironmentManager(metaclass=Singleton):
class EnvironmentManager:

	condaBin = 'micromamba'
	host = 'localhost'
	environments: dict[str, Environment] = {}
	
	def __init__(self, condaPath:str|Path=__file__) -> None:
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

	def _getOutput(self, process):
		outputs = []
		for line in process.stdout:
			logger.info(line)
			if 'CondaSystemExit' in line:
				process.kill()
				raise Exception('An error occured during the execution of the commands {commands}.')
			outputs.append(line)
		process.wait()
		if process.returncode != 0:
			raise Exception('An error occured during the execution of the commands {commands}.')
		return (outputs, process.returncode)

	# If launchMessage is defined: execute until launchMessage is print
	# else: execute completely (blocking)
	def _executeCommands(self, commands: list[str], launchedMessage:str=None, env:dict[str, str]=None, exitIfCommandError=True):
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
		if len(dependencies['conda'])>0:
			process = self._executeCommands([self._activateConda(), f'{self.condaBin} list -y'])
			out, _ = self._getOutput(process)
			installedCondaPackages = out.split('\n')
			if not all([self._removeChannel(d) in installedCondaPackages for d in dependencies['conda']]):
				return True
		dists = [f'{dist.metadata["Name"]}=={dist.version}' for dist in metadata.distributions()]
		return not all([d in dists for d in dependencies['pip']])

	def _isWindows(self):
		return platform.system() == 'Windows'
	
	def _getCondaPaths(self):
		return self.condaPath.resolve(), Path('bin/micromamba' if platform.system() != 'Windows' else 'Library/bin/micromamba.exe')

	def _setupCondaChannels(self):
		return [f'{self.condaBin} config append channels conda-forge', f'{self.condaBin} config append channels nodefaults', f'{self.condaBin} config set channel_priority strict']
		
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
			commands += [f'cd "{condaPath}"', f'curl -Ls https://micro.mamba.pm/api/micromamba/{system}-{machine}/latest | tar -xvj bin/micromamba']
		return commands + self._setupCondaChannels()

	def _activateConda(self):
		# activatePath = Path(self.condaPath) / 'condabin' / 'conda.bat' if self._isWindows() else Path(self.condaPath) / 'etc' / 'profile.d' / 'conda.sh'
		# return f'"{activatePath}" ' if self._isWindows() else f'. "{activatePath}"'
		currentPath = Path.cwd().resolve()
		condaPath, condaBinPath = self._getCondaPaths()
		commands = self._installCondaIfNecessary()
		if platform.system() == 'Windows':
			commands += [f'Set-Location -Path "{condaPath}"', 
				f'$Env:MAMBA_ROOT_PREFIX="{condaPath}"', 
				f'{condaBinPath} shell hook -s powershell | Out-String | Invoke-Expression',
				f'Set-Location -Path "{currentPath}"']
		else:
			commands += [f'cd "{condaPath}"', f'export MAMBA_ROOT_PREFIX="{condaPath}"', f'eval "$({condaBinPath} shell hook -s posix)"', f'cd "{currentPath}"']
		return commands

	def _environmentExists(self, environment:str):
		condaMeta = Path(self.condaPath) / 'envs' / environment / 'conda-meta'
		return condaMeta.is_dir() # we could also check for the condaMeta / history file.
	
	def install(self, environment:str, channel=None):
		channel = channel + '::' if channel is not None else ''
		process = self._executeCommands(self._activateConda() + [f'{self.condaBin} install {channel}{environment} -y'])
		self._getOutput(process)

	def create(self, environment:str, dependencies:Dependencies={}, skipIfDependenciesAreAvailable=False, errorIfExists=False) -> bool:
		if skipIfDependenciesAreAvailable and not self.environmentIsRequired(dependencies): return False
		if self._environmentExists(environment):
			if errorIfExists:
				raise Exception(f'Error: the environment {environment} already exists.')
			else:
				return True
		pythonRequirement = f'python={dependencies["python"]}' if 'python' in dependencies and dependencies['python'] not in ['latest', ''] else 'python'
		condaDependencies = dependencies['conda'] if 'conda' in dependencies else []
		pipDependencies = dependencies['pip'] if 'pip' in dependencies else []
		createEnvCommands = self._activateConda() + [f'{self.condaBin} create -n {environment} {pythonRequirement} {" ".join(condaDependencies)} -y']
		pipInstallCommands = [f'{self.condaBin} activate {environment}', f'pip install {" ".join(pipDependencies)}'] if len(pipDependencies)>0 else []
		process = self._executeCommands(createEnvCommands + pipInstallCommands)
		self._getOutput(process)
		return True
	
	def _environmentIsLaunched(self, environment:str):
		return environment in self.environments and self.environments[environment].launched()
	
	def launch(self, environment:str, customCommand:str=None, environmentVariables:dict[str, str]=None) -> Environment:
		if self._environmentIsLaunched(environment):
			return self.environments[environment]

		moduleCallerPath = Path(__file__).parent / 'ModuleCaller.py'
		commands = self._activateConda() + [
					f'{self.condaBin} activate {environment}', 
					f'python -u "{moduleCallerPath}"' if customCommand is None else customCommand]
		process = self._executeCommands(commands, env=environmentVariables)
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
			return ProxyEnvironment(environment)
	
	def exit(self, environment:Environment|str):
		environmentName = environment if isinstance(environment, str) else environment.name
		if environmentName in self.environments:
			self.environments[environmentName]._exit()
			del self.environments[environmentName]
	
environmentManager = EnvironmentManager()