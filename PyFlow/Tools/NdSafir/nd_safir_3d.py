import subprocess
import sys
import argparse
import json
from pathlib import Path

class Tool:

    categories = ['Denoising']
    dependencies = dict(python='3.9', conda=['bioimageit::ndsafir|osx-64,win-64,linux-64'], pip=[])
    environment = 'ndsafir'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("ND-Safir 3D", description="Denoising method dedicated to microscopy image and sequence analysis.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-n', '--noise', help='Model used to evaluate the noise variance.', default='Gauss', choices=['Gauss', 'Poisson-Gauss', 'Adaptive-Gauss'], type=str)
        inputs_parser.add_argument('-p', '--patch', help='Patch radius. Must be of the form AxBxC where A, B and C are the patch radius in each dimension.', default='7x7x1', type=str)
        inputs_parser.add_argument('-nf', '--noise_factor', help='Noise factor.', default=1, type=float)
        inputs_parser.add_argument('-nit', '--n_iterations', help='Number of iterations.', default=5, type=int)
        inputs_parser.add_argument('-ts', '--time_series', help='Consider the image as a sequence.', action='store_true')
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image.', default='{input_image.stem}_denoised{input_image.exts}', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )
    
    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit('Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Run ND-Safir on image {args.input_image}')
        command = ['ndsafir', '-i', args.input_image, '-o', args.output_image, '-noise', args.noise, '-iter', args.n_iterations, '-nf', args.noise_factor, '-2dt', 1 if args.time_series else 0, '-patch', args.patch]
        subprocess.run([str(c) for c in command])

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)