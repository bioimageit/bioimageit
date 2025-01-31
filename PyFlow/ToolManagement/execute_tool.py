import sys
import argparse
from pathlib import Path
from importlib import import_module
from ToolParser import create_parser

parser = argparse.ArgumentParser('Execute tool', description='Execute a biit tool', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('tool_path', help='Tool path', type=Path)

args = parser.parse_args([sys.argv[1]])
sys.path.append(str(args.tool_path.parent))
module = import_module(args.tool_path.stem)
tool = module.Tool()

parser = create_parser(tool)

args = parser.parse_args(sys.argv[2:])
if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

tool.processData(args)