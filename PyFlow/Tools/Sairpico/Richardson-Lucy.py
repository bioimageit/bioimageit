import sys
import subprocess
from pathlib import Path

class Tool:

    categories = ['Deconvolution']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'
    
    name = "Richardson-Lucy"
    description = "Richardson-Lucy deconvolution."
    inputs = [
            dict(
                names = ['-i', '--input'],
                help = 'Input image (x and y axis should ideally be even numbers)',
                required = True,
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['--type'],
                help = 'Perform 2D, 2D Slice or 3D deconvolution.',
                default = '2D',
                choices = ['2D', '2D Slice', '3D'],
                type = str,
            ),
            dict(
                names = ['--sigma'],
                help = 'Gaussian PSF width (for 2D and 2D Slice only)',
                default = 1.5,
                type = float,
            ),
            dict(
                names = ['--psf'],
                help = 'PSF Image (for 3D only)',
                default = None,
                type = Path,
            ),
            dict(
                names = ['--niter'],
                help = 'Number of iterations',
                default = 15,
                type = int,
            ),
            dict(
                names = ['--lambda'],
                help = 'Regularization parameter (unused in 3D)',
                default = 0,
                type = float,
            ),
            dict(
                names = ['--padding'],
                help = 'Add padding to process border pixels',
                default = False,
                type = bool,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output'],
                help = 'Output path for the deconvolved image.',
                default = '{input.name}_deconvolved{input.exts}',
                type = Path,
            ),
    ]
    
    def processData(self, args):
        print('Performing Richardson-Lucy deconvolution')

        if args.type == '3D' and args.psf is None or not args.psf.exists():
            raise Exception('Error: the argument psf must point to an existing PSF image file, it is set to "{args.psf}" which does not exist.')

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
        subprocess.run([str(ca) for ca in commandArgs], check=True)