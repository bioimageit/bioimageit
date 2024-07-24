from pathlib import Path
from importlib import import_module

from PyFlow.Core import FunctionLibraryBase
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitToolNode import createNode as createToolNode
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitSimpleITKNodes import BinaryThreshold, ExtractChannel, AddScalarToImage, SubtractImages, ConnectedComponents, LabelStatistics

class BiitLib(FunctionLibraryBase):
    """doc string for BiitLib"""
    classes = {}

toolsPath = Path('PyFlow/Tools/')

def getTools(toolsPath):
    return sorted(list(Path(toolsPath).glob('**/*.py')))

def loadTools(toolsPath):
    tools = []
    for modulePath in getTools(toolsPath):
        moduleImportPath = str(modulePath.relative_to(Path()).with_suffix('')).replace('/', '.')
        module = import_module(moduleImportPath)
        tool = createToolNode(modulePath, moduleImportPath, module)
        BiitLib.classes[modulePath.name] = tool
        tools.append(tool)
    return tools

loadTools(toolsPath)

BiitLib.classes['BinaryThreshold'] = BinaryThreshold
BiitLib.classes['AddScalarToImage'] = AddScalarToImage
BiitLib.classes['ExtractChannel'] = ExtractChannel
BiitLib.classes['SubtractImages'] = SubtractImages
BiitLib.classes['ConnectedComponents'] = ConnectedComponents
BiitLib.classes['LabelStatistics'] = LabelStatistics
