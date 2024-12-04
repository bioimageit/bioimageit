import logging
import re
import platform
import tempfile
import threading
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

import psutil

# class Singleton(type):
# 	_instances = {}
# 	def __call__(cls, *args, **kwargs):
# 		if cls not in cls._instances:
# 			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
# 		return cls._instances[cls]
if len(logging.root.handlers)==0: 
	logging.basicConfig()
	
logger = logging.getLogger(__name__)

class ExecutionException(Exception):
	"""Exception raised when the environment raises an error when executing the requested function.

	Attributes:
		message -- explanation of the error
	"""

	def __init__(self, message):
		super().__init__(message)
		self.exception = message['exception'] if 'exception' in message else None
		self.traceback = message['traceback'] if 'traceback' in message else None

class IncompatibilityException(Exception):
    pass

class CustomHandler(logging.Handler):

	def __init__(self, log)-> None:
		logging.Handler.__init__(self=self)
		self.log = log

	def emit(self, record: logging.LogRecord) -> None:
		formatter = self.formatter if self.formatter is not None else logger.handlers[0].formatter if len(logger.handlers)>0 and logger.handlers[0].formatter is not None else logging.root.handlers[0].formatter
		self.log(formatter.format(record))

def attachLogHandler(log:Callable[[str], None], logLevel=logging.INFO) -> None:
	logger.setLevel(logLevel)
	ch = CustomHandler(log)
	ch.setLevel(logLevel)
	logger.addHandler(ch)
	return

class OptionalDependencies(TypedDict):
	conda: NotRequired[list[str]]
	pip: NotRequired[list[str]]
	pip_no_deps: NotRequired[list[str]]

class Dependencies(TypedDict):
	python: str
	conda: NotRequired[list[str]]
	pip: NotRequired[list[str]]
	pip_no_deps: NotRequired[list[str]]
	optional: OptionalDependencies

class Environment():
	
	def __init__(self, name) -> None:
		self.name = name
		self.process = None
		self.installedDependencies = {}

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
		self.stopEvent = threading.Event()
		self.connection = None
		# self.nTries = 0
	
	def initialize(self):
		self.connection = Client((EnvironmentManager.host, self.port))
	
	def execute(self, module:str, function: str, args: list):
		if self.connection.closed:
			logger.warning(f'Connection not ready. Skipping execute {module}.{function}({args})')
			return
		try:
			self.connection.send(dict(action='execute', module=module, function=function, args=args))
			while message := self.connection.recv():
				if message['action'] == 'execution finished':
					logger.info('execution finished')
					return message['result'] if 'result' in message else None
				elif message['action'] == 'error':
					raise ExecutionException(message)
				# if message['action'] == 'print':
				# 	print(message['content'])
				else:
					logger.warning('Got an unexpected message: ', message)
		# If the connection was closed (subprocess killed): catch and ignore the exception, otherwise: raise it
		except EOFError:
			print("Connection closed gracefully by the peer.")
		except BrokenPipeError as e:
			print("Broken pipe. The peer process might have terminated.")
		# except (PicklingError, TypeError) as e:
		# 	print(f"Failed to serialize the message: {e}")
		except OSError as e:
			if e.errno == 9:  # Bad file descriptor
				print("Connection closed abruptly by the peer.")
			else:
				print(f"Unexpected OSError: {e}")
				raise e
		
		# Check that process are launched only once: id?
		# Check that they are properly killed

		# try:
		# except EOFError as e:
		# 	if self.nTries > 1:
		# 		raise e
		# 	self.initialize()
		# 	self.execute(module, function, args)
		# 	self.nTries += 1
	
	def launched(self):
		if self.process is None: return True # can be true in Debug mode
		return self.process.poll() is None and self.connection is not None and self.connection.writable and self.connection.readable and not self.connection.closed
	
	def _exit(self):
		if self.connection is not None:
			try:
				self.connection.send(dict(action='exit'))
			except OSError as e:
				if e.args[0] == 'handle is closed': pass
			self.connection.close()
		if self.process is None: return # can be true in Debug mode
		self.stopEvent.set()
		# self.process.kill()

		# Terminate the process and its children
		parent = psutil.Process(self.process.pid)
		for child in parent.children(recursive=True):  # Get all child processes
			child.kill()
		parent.kill()

		# self.process.wait(timeout=1)

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

	def _getOutput(self, process:subprocess.Popen, commands:list[str], log=True, strip=True):
		prefix = '[...] ' if len(str(commands)) > 150 else ''
		commands = prefix + str(commands)[-150:] if commands is not None and len(commands)>0 else ''
		outputs = []
		for line in process.stdout:
			if strip: 
				line = line.strip()
			if log:
				logger.info(line)
			if 'CondaSystemExit' in line:
				process.kill()
				raise Exception(f'The execution of the commands "{commands}" failed.')
			outputs.append(line)
		process.wait()
		if process.returncode != 0:
			raise Exception(f'The execution of the commands "{commands}" failed.')
		return (outputs, process.returncode)

	def setProxies(self, proxies):
		condaPath, _ = self._getCondaPaths()
		condaConfigPath = condaPath / '.mambarc'
		condaConfig = dict()
		import yaml
		if condaConfigPath.exists():
			with open(condaConfigPath, 'r') as f:
				condaConfig = yaml.safe_load(f)
		condaConfig['proxy_servers'] = proxies
		with open(condaConfigPath, 'w') as f:
			yaml.safe_dump(condaConfig, f)
		
	# If launchMessage is defined: execute until launchMessage is print
	# else: execute completely (blocking)
	def executeCommands(self, commands: list[str], launchedMessage:str=None, env:dict[str, str]=None, exitIfCommandError=True, waitComplete=False, log=True):
		print('executeCommands', commands, launchedMessage)
		rawCommands = commands.copy()
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
			process = subprocess.Popen(executeFile, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, encoding='utf-8', bufsize=1)
			if waitComplete:
				with process:
					return self._getOutput(process, rawCommands, log=log)
			return process

	def _removeChannel(self, condaDependency):
		withoutChannel = condaDependency.split('::')[1] if '::' in condaDependency else condaDependency
		return withoutChannel.split('|')[0] if '|' in withoutChannel else withoutChannel
	
	def dependenciesAreInstalled(self, environment:str, dependencies: Dependencies):
		installedDependencies = self.environments[environment].installedDependencies if environment in self.environments else {}
		if 'conda' in dependencies and len(dependencies['conda'])>0:
			if 'conda' not in installedDependencies:
				installedDependencies['conda'], _ = self.executeCommands(self._activateConda() + [f'{self.condaBin} activate {environment}', f'{self.condaBin} list -y'], waitComplete=True, log=False)
			if not all([self._removeChannel(d) in installedDependencies['conda'] for d in dependencies['conda']]):
				return False
		if ('pip' not in dependencies) and ('pip_no_deps' not in dependencies): return True
		
		if 'pip' not in installedDependencies:
			if environment is not None:
				installedDependencies['pip'], _ = self.executeCommands(self._activateConda() + [f'{self.condaBin} activate {environment}', f'pip freeze'], waitComplete=True, log=False)
			else:
				installedDependencies['pip'] = [f'{dist.metadata["Name"]}=={dist.version}' for dist in metadata.distributions()]

		allPipDepsAreSatisfied = True
		if 'pip' in dependencies: allPipDepsAreSatisfied = allPipDepsAreSatisfied and all([d in installedDependencies['pip'] for d in dependencies['pip']])
		if 'pip_no_deps' in dependencies: allPipDepsAreSatisfied = allPipDepsAreSatisfied and all([d in installedDependencies['pip'] for d in dependencies['pip_no_deps']])
		return allPipDepsAreSatisfied

	def _getPlatformCommonName(self):
		return 'mac' if platform.system() == 'Darwin' else platform.system().lower()
	
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
	
	def install(self, environment:str, package:str, channel=None):
		channel = channel + '::' if channel is not None else ''
		self.executeCommands(self._activateConda() + [f'{self.condaBin} activate {environment}', f'{self.condaBin} install {channel}{package} -y'], waitComplete=True)
		self.environments[environment].installedDependencies = {}
	
	def platformCondaFormat(self):
		machine = platform.machine()
		machine = '64' if machine == 'x86_64' else machine
		return dict(Darwin='osx', Windows='win', Linux='linux')[platform.system()] + '-' + machine

	def formatDependencies(self, package_manager:str, dependencies: list[str], raiseIncompatibilityException=False):
		dependencies = dependencies[package_manager] if package_manager in dependencies else []
		# If there is a "|" in the dependency: check that this platform support this dependency, otherwise ignore it
		finalDependencies = []
		for dependency in dependencies:
			if '|' in dependency:
				dependencyParts = dependency.split('|')
				platforms = [p for p in dependencyParts[-1].split(',')]  # will be a list like ['win-64', 'osx-arm64', 'linux-arm64']
				currentPlatform = self.platformCondaFormat()
				if currentPlatform in platforms:
					finalDependencies.append(dependencyParts[0])
				elif raiseIncompatibilityException:
					platformsString = ', '.join(platforms)
					raise IncompatibilityException(f'Error: the library {dependencyParts[0]} is not available on this platform ({currentPlatform}). It is only available on the following platforms: {platformsString}.')
			else:
				finalDependencies.append(dependency)
		return [f'"{d}"' for d in finalDependencies]
	
	def installDependencies(self, environment:str, dependencies: Dependencies={}, raiseIncompatibilityException=True):
		if any(['::' in d for d in dependencies['pip']]):
			raise Exception(f'One pip dependency has a channel specifier "::" ({dependencies["pip"]}), is it a conda dependency?')
		condaDependencies = self.formatDependencies('conda', dependencies, raiseIncompatibilityException)
		pipDependencies = self.formatDependencies('pip', dependencies, raiseIncompatibilityException)
		pipNoDepsDependencies = self.formatDependencies('pip_no_deps', dependencies, raiseIncompatibilityException)
		if 'optional' in dependencies:
			condaDependencies += self.formatDependencies('conda', dependencies['optional'])
			pipDependencies += self.formatDependencies('pip', dependencies['optional'])
			pipNoDepsDependencies += self.formatDependencies('pip_no_deps', dependencies['optional'])
		installDepsCommands = [f'{self.condaBin} activate {environment}'] if len(condaDependencies) > 0 or len(pipDependencies) > 0 else []
		installDepsCommands += [f'{self.condaBin} install {" ".join(condaDependencies)} -y'] if len(condaDependencies)>0 else []
		installDepsCommands += [f'pip install {" ".join(pipDependencies)}'] if len(pipDependencies)>0 else []
		installDepsCommands += [f'pip install --no-dependencies {" ".join(pipNoDepsDependencies)}'] if len(pipNoDepsDependencies)>0 else []
		if environment in self.environments:
			self.environments[environment].installedDependencies = {}
		return installDepsCommands
	
	def _getCommandsForCurrentPlatfrom(self, additionalCommands:dict[str, list[str]]={}):
		commands = []
		if additionalCommands is not None and 'all' in additionalCommands:
			commands += additionalCommands['all']
		if additionalCommands is not None and self._getPlatformCommonName() in additionalCommands:
			commands += additionalCommands[self._getPlatformCommonName()]
		return commands
	
	def create(self, environment:str, dependencies:Dependencies={}, additionalInstallCommands:dict[str, list[str]]={}, additionalActivateCommands:dict[str, list[str]]={}, mainEnvironment:str=None, errorIfExists=False, raiseIncompatibilityException=True) -> bool:
		if mainEnvironment is not None and self.dependenciesAreInstalled(mainEnvironment, dependencies): return False
		if self.environmentExists(environment):
			if errorIfExists:
				raise Exception(f'Error: the environment {environment} already exists.')
			else:
				return True
		pythonVersion = str(dependencies['python']).replace('=', '') if 'python' in dependencies and dependencies['python'] else ''
		match = re.search(r'(\d+)\.(\d+)', pythonVersion)
		if match and int(match.group(1))<3 or (match.group(2))<9:
			raise Exception('Python version must be greater than 3.8')
		pythonRequirement = ' python=' + pythonVersion if len(pythonVersion)>0 else ''
		createEnvCommands = self._activateConda() + [f'{self.condaBin} create -n {environment}{pythonRequirement} -y']
		createEnvCommands += self.installDependencies(environment, dependencies, raiseIncompatibilityException)
		createEnvCommands += self._getCommandsForCurrentPlatfrom(additionalInstallCommands)
		createEnvCommands += self._getCommandsForCurrentPlatfrom(additionalActivateCommands)
		self.executeCommands(createEnvCommands, waitComplete=True)
		return True
	
	def environmentIsLaunched(self, environment:str):
		return environment in self.environments and self.environments[environment].launched()
	
	# Unusued, but could be nice
	# def executeCommandsInEnvironment(self, environment:str, commands:list[str], environmentVariables:dict[str, str]=None):
	# 	commands = self._activateConda() + [f'{self.condaBin} activate {environment}'] + commands
	# 	return self.executeCommands(commands, env=environmentVariables)

	def launch(self, environment:str, customCommand:str=None, environmentVariables:dict[str, str]=None, condaEnvironment=True, additionalActivateCommands:dict[str, list[str]]={}) -> Environment:
		if self.environmentIsLaunched(environment):
			return self.environments[environment]

		moduleCallerPath = Path(__file__).parent / 'ModuleCaller.py'
		commands = self._activateConda() + [f'{self.condaBin} activate {environment}'] if condaEnvironment else []
		commands += self._getCommandsForCurrentPlatfrom(additionalActivateCommands)
		commands += [f'python -u "{moduleCallerPath}"' if customCommand is None else customCommand]
		debug = False # environment == 'napari' # customCommand is not None and 'NapariManager' in customCommand
		port = -1 if not debug else 60873 # Replace port number by the one you get when you debug ModuleCaller.py ; see PyFlow/ToolManagement/.vscode/launch.json
		process = self.executeCommands(commands, env=environmentVariables) if not debug else None
		# The python command is called with the -u (unbuffered) option, we can wait for a specific print before letting the process run by itself
		# if the unbuffered option is not set, the following can wait for the whole python process to finish
		if not debug:
			try:
				for line in process.stdout:
					logger.info(line)
					if line.strip().startswith('Listening port '):
						port = int(line.strip().replace('Listening port ', ''))
						break
			except Exception as e:
				process.stdout.close()
				raise e
			# If process is finished: check if error
			if process.poll() is not None:
				process.stdout.close()
				raise Exception(f'Process exited with return code {process.returncode}.')
		ce = ClientEnvironment(environment, port, process)
		self.environments[environment] = ce
		ce.initialize()
		return ce
	
	# @contextmanager
	def createAndLaunch(self, environment:str, dependencies:Dependencies={}, customCommand:str=None, environmentVariables:dict[str, str]=None, additionalInstallCommands:dict[str, list[str]]={}, additionalActivateCommands:dict[str, list[str]]={}, mainEnvironment:str=None, raiseIncompatibilityException=True) -> Environment:
		environmentIsRequired = self.create(environment, dependencies, additionalInstallCommands=additionalInstallCommands, additionalActivateCommands=additionalActivateCommands, mainEnvironment=mainEnvironment, raiseIncompatibilityException=raiseIncompatibilityException)
		if environmentIsRequired:
			return self.launch(environment, customCommand, environmentVariables=environmentVariables, additionalActivateCommands=additionalActivateCommands)
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