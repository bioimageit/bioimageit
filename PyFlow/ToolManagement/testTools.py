from importlib import import_module
from pathlib import Path
from PyFlow import getImportPath, getBundlePath
from PyFlow.ToolManagement.EnvironmentManager import environmentManager, Environment, attachLogHandler
environmentManager.setCondaPath(getBundlePath() / 'micromamba')

toolsPath = Path('PyFlow/Tools/')

def getTools(toolsPath):
    return sorted(list(Path(toolsPath).glob('*/*.py')))

def logOutput(process):
    for line in process.stdout:
        print(line)

def testTools(toolsPath):

    for toolPath in getTools(toolsPath):
        moduleImportPath = getImportPath(toolPath)
        module = import_module(moduleImportPath)
        if hasattr(module.Tool, 'test'):
            
            additionalInstallCommands = module.Tool.additionalInstallCommands if hasattr(module.Tool, 'additionalInstallCommands') else None
            environment = environmentManager.createAndLaunch(module.Tool.environment, module.Tool.dependencies, additionalInstallCommands=additionalInstallCommands, mainEnvironment='bioimageit')
            
            if environment.process is not None:
                logOutput(environment.process)
            
            outputFolderPath = (toolPath / 'test-data').resolve()

            environment.execute('PyFlow.ToolManagement.ToolBase', 'processData', [moduleImportPath, module.Tool.test, outputFolderPath])
                

testTools(toolsPath)