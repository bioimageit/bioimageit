import os
from importlib import import_module

tool = None
moduleImportPath = None

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

def initialize(newModuleImportPath: str, args: list[str]):
    global tool, moduleImportPath
    toolMustBeImported = moduleImportPath != newModuleImportPath
    if toolMustBeImported:
        module = import_module(newModuleImportPath)
        tool = module.Tool()
        moduleImportPath = newModuleImportPath
    parser, _ = tool.getArgumentParser()
    parser.exit_on_error = False
    args = parser.parse_args(args)
    if toolMustBeImported and hasattr(tool, 'initialize') and callable(tool.initialize):
        tool.initialize(args)
    return tool, args

def processData(moduleImportPath: str, args: list[str], nodeOutputPath):
    tool, args = initialize(moduleImportPath, args)
    currentDirectory = os.getcwd()
    result = None
    if hasattr(tool, 'processData') and callable(tool.processData):
        os.chdir(nodeOutputPath)
        result = tool.processData(args)
        os.chdir(currentDirectory)
    return result

# def processAllData(moduleImportPath: str, argsList: list[list[str]]):
#     tool, args = initialize(moduleImportPath, argsList[0])
#     tool.processAllData(args)

def processAllData(moduleImportPath: str, argsList: list[dict], nodeOutputPath):
    # Initialize with the args of the first row, convert them to a list of string before use
    args0 = [item for items in [(f'--{key}',) if isinstance(value, bool) and value else (f'--{key}', f'{value}') for key, value in argsList[0].items()] for item in items]
    tool, _ = initialize(moduleImportPath, args0)
    nodeOutputPath.mkdir(exist_ok=True, parents=True)
    currentDirectory = os.getcwd()
    result = None
    if hasattr(tool, 'processAllData') and callable(tool.processAllData):
        os.chdir(nodeOutputPath)
        result = tool.processAllData(dict2obj(argsList))
        os.chdir(currentDirectory)
    return result