import argparse
import subprocess
import sys
from pathlib import Path
from .core import ndsafir_series

class Tool:

    categories = ['Denoising']
    dependencies = dict(python='3.9', conda=['bioimageit::ndsafir|osx-64,win-64,linux-64'], pip=[])
    environment = 'ndsafir'
    test = ['--input_image', '03_rab_bruite.tif', '--type', '3D', '-n', 'Adaptive-Gauss', '-nf', '2', '--output_image', 'DN.tif']

    noiseChoices = ['Gauss', 'Poisson-Gauss', 'Adaptive-Gauss']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("ND-Safir", description="Denoising method dedicated to microscopy image and sequence analysis.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-t', '--type', choices=['2D', '3D', '4D'], help="Perform 2D, 3D or 3D + time denoising.", default='2D', type=str)
        inputs_parser.add_argument('-n', '--noise', help='Model used to evaluate the noise variance.', default='Gauss', choices=Tool.noiseChoices, type=str)
        inputs_parser.add_argument('-p', '--patch', help='Patch radius. Must be of the form AxB (for 2D) or AxBxC (for 3D) where A, B and C are the patch radius in each dimension.', default='7x7x1', type=str)
        inputs_parser.add_argument('-nf', '--noise_factor', help='Noise factor.', default=1, type=float)
        inputs_parser.add_argument('-nit', '--n_iterations', help='Number of iterations.', default=5, type=int)
        inputs_parser.add_argument('-ts', '--time_series', help='Consider the image as a sequence (for 3D only).', action='store_true')
        inputs_parser.add_argument('-nfr', '--n_frames', help='Number of frames to process in a batch. Use 0 to process everything at once (for 4D only).', default=0)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image.', default='{input_image.stem}_denoised{input_image.exts}', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        noise = Tool.noiseChoices.index(args.noise)
        print(f'[[1/1]] Run ND-Safir on image {args.input_image}')
        if args.type == '4D':
            ndsafir_series.ndsafir_series(args.input_image, args.output_image, noise, args.n_iterations, args.noise_factor, args.patch, args.n_frames)
        else:
            command = ['ndsafir', '-i', args.input_image, '-o', args.output_image, '-noise', noise, '-iter', args.n_iterations, '-nf', args.noise_factor, '-2dt', 1 if args.time_series and args.type != '2D' else 0, '-patch', args.patch]
            return subprocess.run([str(c) for c in command])

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args, _ = parser.parse_args()
    tool.processData(args)