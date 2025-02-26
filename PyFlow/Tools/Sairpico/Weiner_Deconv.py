from pathlib import Path
import subprocess
class Tool:

    categories = ['Deconvolution']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'
    
    name = "Wiener Deconv"
    description = "Wiener deconvolution"
    inputs = [
            dict(
                name = 'input',
                help = 'Input Image',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'type',
                help = 'Perform 2D, 2D Slice or 3D deconvolution.',
                default = '2D',
                choices = ['2D', '2D Slice', '3D'],
                type = 'str',
            ),
            dict(
                name = 'sigma',
                help = 'Gaussian PSF width (for 2D and 2D Slice only)',
                default = 1.5,
                type = 'float',
            ),
            dict(
                name = 'psf',
                help = 'PSF Image (for 3D only)',
                default = None,
                type = 'Path',
            ),
            dict(
                name = 'lambda',
                help = 'Regularization parameter',
                default = 0.01,
                type = 'float',
            ),
            dict(
                name = 'padding',
                help = 'Add padding to process border pixels',
                default = False,
                type = 'bool',
            ),
    ]
    outputs = [
            dict(
                name = 'output',
                shortname = 'o',
                help = 'Output path for the denoised image.',
                default = '{input.name}_deconvolved{input.exts}',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        print('Performing Wiener deconvolution')
        
        commandArgs = [
            'simgwiener' + args.type.replace(' ', '').lower(), '-i', args.input, '-o', args.output,
            '-lambda', getattr(args, 'lambda'), '-padding', 'true' if args.padding else 'false'
        ]
        if  args.type != '3D':
            commandArgs += ['-sigma', args.sigma]
        else:
            commandArgs += ['-psf', args.psf]
        subprocess.run([str(ca) for ca in commandArgs], check=True)

