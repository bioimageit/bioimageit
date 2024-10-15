import subprocess
import sys
import argparse
from pathlib import Path

class Tool:

    categories = ['Detection']
    dependencies = dict(conda=['bioimageit::atlas'], pip=[])
    environment = 'atlas'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Atlas", description="ATLAS is a new spot detection method. The spots size is automatically selected and the detection threshold adapts to the local image dynamics.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path. The width and height of the image should be even for best results.', required=True, type=Path)
        inputs_parser.add_argument('-rad', '--gaussian_std', help='Standard deviation of the Gaussian window (0 for global threshold).', default=60, type=int)
        inputs_parser.add_argument('-pval', '--p_value', help='P-value to account for the probability of false detection.', default=0.001, type=float)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image.', default='{input_image.stem}_detections{input_image.exts}', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )
    
    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit('Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Run Atlas on image {args.input_image}')
        command = ['atlas', '-i', args.input_image, '-o', args.output_image, '-rad', args.gaussian_std, '-pval', args.p_value]
        subprocess.run([str(c) for c in command])

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)