import threading
import json
import unittest
import logging
import shutil
from importlib import import_module
from pathlib import Path
from PyFlow.ToolManagement.ToolParser import create_parser
from PyFlow import getImportPath, getRootPath
from PyFlow.ToolManagement.EnvironmentManager import environmentManager, Environment, attachLogHandler, IncompatibilityException

environmentManager.setCondaPath(getRootPath() / 'micromamba')
# environmentManager.environments['bioimageit'] = DirectEnvironment('bioimageit')  # Initialize default installed dependencies for the bioimageit env
# environment = environmentManager.launch('bioimageit')

toolsPath = Path('PyFlow/Tools/')

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'tests.log', mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def logLine(line):
    # print(line)
    logger.info(line.msg if isinstance(line, logging.LogRecord) else str(line))

attachLogHandler(logLine)

import subprocess

def get_git_revision_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()

def getTools(toolsPath):
    return sorted(list(Path(toolsPath).glob('*/*.py')))

def logOutput(process):
    print(f'logging process output')
    with process.stdout:
        for line in process.stdout:
            print(line)

class TestGeneral(unittest.TestCase):
    def setUp(self):
        print("\t[BEGIN TEST]", self._testMethodName)

    def test_tools(self):
        toolValidationPath = Path(__file__).parent / 'validated_tools.json'
        validated_tools = []
        if toolValidationPath.exists():
            with open(toolValidationPath, 'r') as f:
                validated_tools_data = json.load(f)
                validated_tools = validated_tools_data['validated_tools']
                if get_git_revision_hash() != validated_tools_data['git_revision_hash']:
                    shutil.copyfile(toolValidationPath, toolValidationPath.parent / f'{toolValidationPath.stem}_{validated_tools_data["git_revision_hash"]}.json')
                    validated_tools = []

        for toolPath in getTools(toolsPath):
            moduleImportPath = getImportPath(toolPath)
            if moduleImportPath in validated_tools: continue
            module = import_module(moduleImportPath)
            if not hasattr(module, 'Tool'): continue
            print(f'\n==============================')
            print(f'==============================')
            print(f'Test {moduleImportPath}')
            print(f'Path: {toolPath}')
            if hasattr(module.Tool, 'test'):
                
                additionalInstallCommands = module.Tool.additionalInstallCommands if hasattr(module.Tool, 'additionalInstallCommands') else None
                additionalActivateCommands = module.Tool.additionalActivateCommands if hasattr(module.Tool, 'additionalActivateCommands') else None
                try:
                    environment: Environment = environmentManager.createAndLaunch(module.Tool.environment, module.Tool.dependencies, 
                additionalInstallCommands=additionalInstallCommands, additionalActivateCommands=additionalActivateCommands, mainEnvironment='bioimageit')
                except IncompatibilityException:
                    import platform
                    print(f'Tool {toolPath} not tested since it is not available on this platform ({platform.system()} {platform.machine()})')
                    continue

                if environment.process is not None:
                    thread = threading.Thread(target=logOutput, args=[environment.process])
                    thread.daemon = True
                    thread.start()
                
                print(f'executing processData')

                nodeOutputPath = (toolPath.parent / 'test-data').resolve()

                try:
                    parser = create_parser(module.Tool)
                    args = vars(parser.parse_args(module.Tool.test))
                    environment.execute('PyFlow.ToolManagement.ToolBase', 'processData', [moduleImportPath, args, nodeOutputPath, toolPath])
                    
                    validated_tools.append(moduleImportPath)
                    with open(toolValidationPath, 'w') as f:
                        json.dump(dict(git_revision_hash=get_git_revision_hash(), validated_tools=validated_tools), f)
                except Exception as e:
                    raise e


# testTools(toolsPath)
if __name__ == "__main__":
    unittest.main()
