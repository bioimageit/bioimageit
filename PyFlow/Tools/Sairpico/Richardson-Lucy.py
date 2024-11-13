import sys
import argparse
from pathlib import Path

class Tool:

    categories = ['Deconvolution']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Richardson-Lucy", description="Richardson-Lucy deconvolution.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')

        inputs_parser.add_argument("-i", "--input", type=Path, required=True, help="Input image (x and y axis should ideally be even numbers)")
        inputs_parser.add_argument("--type", choices=['2D', '2D Slice', '3D'], help="Perform 2D, 2D Slice or 3D deconvolution.", default='2D', type=str)
        inputs_parser.add_argument("--sigma", type=float, help="Gaussian PSF width (for 2D and 2D Slice only)", default=1.5)
        inputs_parser.add_argument("--psf", type=Path, help="PSF Image (for 3D only)")
        inputs_parser.add_argument("--niter", type=int, help="Number of iterations", default=15)
        inputs_parser.add_argument("--lambda", type=float, help="Regularization parameter (unused in 3D)", default=0)
        inputs_parser.add_argument("--padding", action='store_true', help="Add padding to process border pixels")

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument("-o", "--output", help="Output path for the deconvolved image.", default="{input.name}_deconvolved{input.exts}", type=Path)
        return parser, dict(input=dict(autoColumn=True))

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        print('Performing Richardson-Lucy deconvolution')
        import subprocess

        if args.type == '3D' and args.psf is None or not args.psf.exists():
            sys.exit('Error: the argument psf must point to an existing PSF image file, it is set to "{args.psf}" which does not exist.')

        commandArgs = [
            'simgrichardsonlucy' + args.type.replace(' ', '').lower(),
            '-i', args.input,
            '-o', args.output,
            '-niter', args.niter,
            '-padding', 'true' if args.padding else 'false'
        ]
        if  args.type != '3D':
            commandArgs += ['-sigma', args.sigma]
        else:
            commandArgs += ['-psf', args.psf, '-lambda', getattr(args, 'lambda')]
        return subprocess.run([str(ca) for ca in commandArgs])

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)
