import os, sys
from pathlib import Path
from importlib import import_module
from PyFlow.ToolManagement.ToolParser import create_parser

tool = None
moduleImportPath = None
currentDirectory = os.getcwd()

def dict2obj(d):
     
    # checking whether object d is a
    # instance of class list
    if isinstance(d, list):
           d = [dict2obj(x) for x in d] 
 
    # if d is not a instance of dict then
    # directly object is returned
    if not isinstance(d, dict):
           return d
  
    # declaring a class
    class C:
        pass
  
    # constructor of the class passed to obj
    obj = C()
  
    for k in d:
        obj.__dict__[k] = dict2obj(d[k])
  
    return obj

def initialize(newModuleImportPath: str, args: list[str], toolsPath:Path):
    global tool, moduleImportPath
    toolMustBeImported = moduleImportPath != newModuleImportPath
    if toolMustBeImported:
        if toolsPath not in sys.path:
            sys.path.append(str(toolsPath))
        # if '/Users/amasson/BioImageIT/Tau Proteins Microtubules Interaction/Tools' not in sys.path:
        #   sys.path.append('/Users/amasson/BioImageIT/Tau Proteins Microtubules Interaction/Tools')
        module = import_module(newModuleImportPath)
        tool = module.Tool()
        moduleImportPath = newModuleImportPath
    parser = create_parser(tool)
    parser.exit_on_error = False
    args = parser.parse_args(args)
    if toolMustBeImported and hasattr(tool, 'initialize') and callable(tool.initialize):
        tool.initialize(args)
    return tool, args

def processData(moduleImportPath: str, args: list[str], nodeOutputPath:Path, toolsPath:Path):
    tool, args = initialize(moduleImportPath, args, toolsPath)
    result = None
    if hasattr(tool, 'processData') and callable(tool.processData):
        os.chdir(nodeOutputPath)
        result = tool.processData(args)
        os.chdir(currentDirectory)
    return result

# def processAllData(moduleImportPath: str, argsList: list[list[str]]):
#     tool, args = initialize(moduleImportPath, argsList[0])
#     tool.processAllData(args)

# def argToList(argList: dict):
#     return [item for items in [(f'--{key}',) if isinstance(value, bool) and value else (f'--{key}', f'{value}') for key, value in argList.items()] for item in items]

def processAllData(moduleImportPath: str, argsList: list[dict], nodeOutputPath:Path, toolsPath:Path):
    # Initialize with the args of the first row, convert them to a list of string before use
    # args0 = argToList(argsList[0])
    args0 = argsList[0]
    tool, _ = initialize(moduleImportPath, args0, toolsPath)
    parser = create_parser(tool)
    nodeOutputPath.mkdir(exist_ok=True, parents=True)
    currentDirectory = os.getcwd()
    result = None
    if hasattr(tool, 'processAllData') and callable(tool.processAllData):
        os.chdir(nodeOutputPath)
        result = tool.processAllData([parser.parse_args(a) for a in argsList]) # dict2obj(argsList))
        os.chdir(currentDirectory)
    return result