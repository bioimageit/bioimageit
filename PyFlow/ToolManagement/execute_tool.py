import sys
import argparse
from pathlib import Path
from importlib import import_module
from ToolParser import create_parser

# ipy execute_tool.py /Users/amasson/Travail/bioimageit/PyFlow/Tools/Cellpose/cellpose_segment.py --input_image  /Users/amasson/Travail/bioimageit/PyFlow/Tools/Cellpose/test-data/img02.png --segmentation  /Users/amasson/Travail/bioimageit/PyFlow/Tools/Cellpose/test-data/img02_segmentation.png --visualization  /Users/amasson/Travail/bioimageit/PyFlow/Tools/Cellpose/test-data/img02_segmentation.npy

parser = argparse.ArgumentParser('Execute tool', description='Execute a biit tool. Example usage: python execute_tool.py /path/to/PyFlow/Tools/Tool/tool.py --arg1 value1 --arg2 value2', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('tool_path', help='Path to the python file of the tool (e.g. /path/to/tool.py ).', type=Path)


args = parser.parse_args([sys.argv[1]])
# Add bioimageit sources to path to be able to import PyFlow.*
bioimageitSourcesPath = Path(__file__).parent.parent.parent.resolve()
sys.path.append(str(bioimageitSourcesPath))
sys.path.append(str(args.tool_path.parent))
module = import_module(args.tool_path.stem)
tool = module.Tool()

parser = create_parser(tool)

args = vars(parser.parse_args(sys.argv[2:]))
if hasattr(tool, 'initialize') and callable(tool.initialize):
    tool.initialize(args)

if hasattr(tool, 'processAllData') and callable(tool.processAllData):
    tool.processAllData([args])

if hasattr(tool, 'processData') and callable(tool.processData):
    tool.processData(args)