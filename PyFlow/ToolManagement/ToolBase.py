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
    tool, args = initialize(moduleImportPath, args)
    tool.processData(args)