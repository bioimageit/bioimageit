from importlib import import_module

tool = None
moduleImportPath = None

def initialize(newModuleImportPath: str, args: list[str]):
    global tool, moduleImportPath
    toolMustBeImported = moduleImportPath != newModuleImportPath
    if toolMustBeImported:
        module = import_module(newModuleImportPath)
        tool = module.Tool()
        moduleImportPath = newModuleImportPath
    parser = tool.getArgumentParser()
    parser.exit_on_error = False
    args = parser.parse_args(args)
    if toolMustBeImported and hasattr(tool, 'initialize') and callable(tool.initialize):
        tool.initialize(args)
    return tool, args

def processData(moduleImportPath: str, args: list[str]):
    if hasattr(tool, 'processData') and callable(tool.processData):
        tool, args = initialize(moduleImportPath, args)
        tool.processData(args)

# def processAllData(moduleImportPath: str, argsList: list[list[str]]):
#     tool, args = initialize(moduleImportPath, argsList[0])
#     tool.processAllData(args)

def processAllData(moduleImportPath: str, argsList: list[dict]):
    if hasattr(tool, 'processAllData') and callable(tool.processAllData):
        # Initialize with the args of the first row, convert them to a list of string before use
        args0 = [item for items in [(f'--{key}',) if isinstance(value, bool) and value else (f'--{key}', f'{value}') for key, value in argsList[0].items()] for item in items]
        tool, _ = initialize(moduleImportPath, args0)
        tool.processAllData(argsList)