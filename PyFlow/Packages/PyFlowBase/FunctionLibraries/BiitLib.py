import sys
from pathlib import Path
from importlib import import_module

from PyFlow import getImportPath
from PyFlow.Core import FunctionLibraryBase
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitToolNode import createNode

class BiitLib(FunctionLibraryBase):
    """doc string for BiitLib"""
    classes = {}

toolsPath = Path('PyFlow/Tools/')

def getTools(toolsPath):
    return sorted(list(Path(toolsPath).glob('*/*.py')))

def loadTools(toolsPath):
    tools = []
    for toolPath in getTools(toolsPath):
        moduleImportPath = getImportPath(toolPath)
        module = import_module(moduleImportPath)
        tool = createNode(toolPath, moduleImportPath, module)
        if tool is not None:
            BiitLib.classes[toolPath.name] = tool
            tools.append(tool)
    return tools

loadTools(toolsPath)
