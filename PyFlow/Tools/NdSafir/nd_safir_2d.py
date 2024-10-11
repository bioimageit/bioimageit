import subprocess
import sys
import argparse
import json
from pathlib import Path

class Tool:

    categories = ['Denoising']
    dependencies = dict(python='3.9', conda=['bioimageit::ndsafir'], pip=[])
    environment = 'ndsafir'
    autoInputs = ['input_image']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("ND-Safir 2D", description="Denoising method dedicated to microscopy image analysis.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-n', '--noise', help='Model used to evaluate the noise variance.', default='Gauss', choices=['Gauss', 'Poisson-Gauss', 'Adaptive-Gauss'], type=str)
        inputs_parser.add_argument('-p', '--patch', help='Patch radius. Must be of the form AxB where A and B are the patch radius in each dimension.', default='7x7', type=str)
        inputs_parser.add_argument('-nf', '--noise_factor', help='Noise factor.', default=1, type=float)
        inputs_parser.add_argument('-nit', '--n_iterations', help='Number of iterations.', default=5, type=int)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image.', default='{input_image.stem}_denoised{input_image.exts}', type=Path)
        return parser
    
    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit('Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Run ND-Safir on image {args.input_image}')
        command = ['ndsafir', '-i', args.input_image, '-o', args.output_image, '-noise', args.noise, '-iter', args.n_iterations, '-nf', args.noise_factor, '-2dt', '0', '-patch', args.patch]
        subprocess.run([str(c) for c in command])

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)