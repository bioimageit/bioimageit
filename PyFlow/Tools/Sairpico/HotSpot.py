import argparse
from pathlib import Path
import subprocess

class Tool:
    categories = ['Sairpico', 'Detection']
    dependencies = dict(python='3.9', conda=['bioimageit::hotspot==1.0.0'], pip=[])
    environment = 'hotspot'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Hotspot Detection", description="Hotspot detection in microscopy images.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        
        # Input arguments
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument("--input_image", type=Path, help="Input Image", required=True)
        inputs_parser.add_argument("--patch_size", type=int, help="Patch size (radius)", default=3)
        inputs_parser.add_argument("--neighborhood_size", type=int, help="Neighborhood size (radius)", default=5)
        inputs_parser.add_argument("--p_value", type=float, help="p-value for false alarm", default=0.2)
        
        # Output arguments
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument("-o", "--output", help="Output path for the detected hotspots image.", default="{input_image.stem}_hotspot.{input_image.exts}", type=Path)
        
        return parser, dict(input_image=dict(autoColumn=True))

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        print("Running hotspot detection on the image")
        commandArgs = [
            'hotSpotDetection', '-i', str(args.input_image), '-o', str(args.output),
            '-m', str(args.patch_size), '-n', str(args.neighborhood_size), '-pv', str(args.p_value)
        ]
        return subprocess.run(commandArgs)

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)
