import os, sys
from pathlib import Path
from importlib import import_module
from contextlib import contextmanager

tool = None
moduleImportPath = None
class DictToObject(object):
    def __init__(self, d):
        for key, value in d.items():
            if isinstance(value, dict):
                setattr(self, key, DictToObject(value))
            else:
                setattr(self, key, value)

@contextmanager
def safe_chdir(path):
    currentPath = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(currentPath)

def initialize(newModuleImportPath: str, args: dict, toolsPath:Path):
    global tool, moduleImportPath
    toolMustBeImported = moduleImportPath != newModuleImportPath
    if toolMustBeImported:
        if toolsPath not in sys.path:
            sys.path.append(str(toolsPath))
        module = import_module(newModuleImportPath)
        tool = module.Tool()
        moduleImportPath = newModuleImportPath
    if toolMustBeImported and hasattr(tool, 'initialize') and callable(tool.initialize):
        tool.initialize(args)
    return tool, args

def processData(moduleImportPath: str, args: dict, nodeOutputPath:Path, toolsPath:Path):
    args = DictToObject(args)
    tool, args = initialize(moduleImportPath, args, toolsPath)
    result = None
    if hasattr(tool, 'processData') and callable(tool.processData):
        with safe_chdir(nodeOutputPath):
            result = tool.processData(args)
    return result

def processAllData(moduleImportPath: str, argsList: list[dict], nodeOutputPath:Path, toolsPath:Path):
    # Initialize with the args of the first row, convert them to a list of string before use
    result = None
    if len(argsList) == 0: return result
    argsList = [DictToObject(args) for args in argsList]
    tool, _ = initialize(moduleImportPath, argsList[0], toolsPath)
    nodeOutputPath.mkdir(exist_ok=True, parents=True)
    if hasattr(tool, 'processAllData') and callable(tool.processAllData):
        with safe_chdir(nodeOutputPath):
            result = tool.processAllData(argsList)
    return result