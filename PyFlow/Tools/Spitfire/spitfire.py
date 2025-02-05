import subprocess
import sys
import argparse
import json
from pathlib import Path

class Tool:

    categories = ['Denoising']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Spitfire", description="SPITFIR(e) utilizes the primal-dual optimization principle for fast energy minimization. Experimental results in various microscopy modalities from wide field up to lattice light sheet demonstrate the ability of the SPITFIR(e) algorithm to efficiently reduce noise, blur, and out-of-focus background, while avoiding the emergence of deconvolution artifacts.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path. The dimensions (width, height, depth) of the image should be even for best results.', required=True, type=Path)
        inputs_parser.add_argument("--type", choices=['2D', '3D', '4D'], help="Perform 2D, 3D or 4D deconvolution.", default='2D', type=str)
        inputs_parser.add_argument('-r', '--regularization', help='Regularization parameter pow(2,-x).', default=2, type=float)
        inputs_parser.add_argument('-w', '--weighting', help='Weighting. Regularization parameter pow(2,-x). Must be in range [0.0, 1.0].', default=0.6, type=float)
        inputs_parser.add_argument('-m', '--method', help='Method.', default='Hessian variation', type=str, choices=['Sparse variation', 'Hessian variation'])
        inputs_parser.add_argument('-p', '--padding', help='Add a padding to process pixels in borders.', action='store_true')
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image.', default='{input_image.stem}_denoised{input_image.exts}', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )
    def processData(self, args):
        if not args.input_image.exists():
            sys.exit(f'Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Run Spitfire on image {args.input_image}')
        process = 'simgspitfiredenoise' + args.type.lower()
        command = [process, '-i', args.input_image, '-o', args.output_image, '-regularization', args.regularization, '-weighting', args.weighting, '-method', 'SV' if args.method == 'Sparse variation' else 'HV', '-padding', 'True' if args.padding else 'False', '-niter', 200]
        subprocess.run([str(c) for c in command])

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)