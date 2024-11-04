import threading
import unittest
from importlib import import_module
from pathlib import Path
from PyFlow import getImportPath, getBundlePath
from PyFlow.ToolManagement.EnvironmentManager import environmentManager, Environment, attachLogHandler
environmentManager.setCondaPath(getBundlePath() / 'micromamba')

toolsPath = Path('PyFlow/Tools/')

def getTools(toolsPath):
    return sorted(list(Path(toolsPath).glob('*/*.py')))

def logOutput(process):
    print(f'logging process output')
    for line in process.stdout:
        print(line)

class TestGeneral(unittest.TestCase):
    def setUp(self):
        print("\t[BEGIN TEST]", self._testMethodName)

    def test_tools(self):

        for toolPath in getTools(toolsPath):
            moduleImportPath = getImportPath(toolPath)
            module = import_module(moduleImportPath)

            if hasattr(module.Tool, 'test'):
                
                additionalInstallCommands = module.Tool.additionalInstallCommands if hasattr(module.Tool, 'additionalInstallCommands') else None
                environment = environmentManager.createAndLaunch(module.Tool.environment, module.Tool.dependencies, additionalInstallCommands=additionalInstallCommands, mainEnvironment='bioimageit')
                
                if environment.process is not None:
                    thread = threading.Thread(target=logOutput, args=[environment.process])
                    thread.daemon = True
                    thread.start()
                
                print(f'executing processData')

                outputFolderPath = (toolPath.parent / 'test-data').resolve()

                environment.execute('PyFlow.ToolManagement.ToolBase', 'processData', [moduleImportPath, module.Tool.test, outputFolderPath])

# testTools(toolsPath)
if __name__ == "__main__":
    unittest.main()
