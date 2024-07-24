from pathlib import Path
from importlib import import_module

tool = None

def initialize(moduleImportPath: str, args: list[str]):
    global tool
    toolIsNone = tool is None
    if toolIsNone:
        module = import_module(moduleImportPath)
        tool = module.Tool()
    parser = tool.getArgumentParser()
    parser.exit_on_error = False
    args = parser.parse_args(args)
    if toolIsNone:
        tool.initialize(args)
    return tool, args

def processData(moduleImportPath: str, args: list[str]):
    tool, args = initialize(moduleImportPath, args)
    tool.processData(args)